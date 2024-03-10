import * as vscode from 'vscode';
import * as childProcess from 'child_process';
import { PythonExtension } from '@vscode/python-extension';
import { promisify } from 'util';
import { stderr } from 'process';

const execFile = promisify(childProcess.execFile);

function getExecFolder(): string {
  const config = vscode.workspace.getConfiguration('string-fixer');

  const folder: string | undefined = config.get('folder');
  // do this rather than `config.has` because typescript compiler
  if (folder) {
    return folder;
  }
  if (vscode.workspace.workspaceFolders) {
    return vscode.workspace.workspaceFolders[0].uri.fsPath;
  }
  throw new Error('cannot find suitable execution folder');
}

async function getPythonExe(): Promise<string> {
  const api = await PythonExtension.api();
  const envPath = await api.environments.getActiveEnvironmentPath();
  let env = await api.environments.resolveEnvironment(envPath);
  const exe = env?.executable?.uri?.fsPath;
  if (!exe) {
    throw new Error('failed to get python interpreter');
  }
  return exe;
}

async function runStringFixer(cmdArgs?: string[]) {
  let execFolder: string;
  let python: string;
  try {
    execFolder = getExecFolder();
    python = await getPythonExe();
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'There was an unidentified error';
    vscode.window.showErrorMessage(message);
    return;
  }
  const args = ['-m', 'string_fixer', '-c', execFolder].concat(
    ...(cmdArgs || []),
  );
  logger?.info(`running string-fixer with args: ${args}`);
  // Execute the Python script
  return execFile(python, args, {
    cwd: execFolder,
  });
}

enum FormatterOpts {
  RUFF = 'ruff',
  BLACK = 'black',
}

async function runPreFormatter() {
  const config = vscode.workspace.getConfiguration('string-fixer');
  const preFormatter: FormatterOpts | undefined = config.get('preFormatter');
  logger?.info(`pre-formatter: ${preFormatter}`);
  if (preFormatter === FormatterOpts.RUFF) {
    if (vscode.extensions.getExtension('charliermarsh.ruff') === undefined) {
      vscode.window.showWarningMessage(
        'Skipping pre-format stage: Ruff extension not installed',
      );
      logger?.warn('charliermarsh.ruff not installed. Skip pre-format');
    } else {
      logger?.info('running ruff.executeFormat');
      await vscode.commands.executeCommand('ruff.executeFormat');
    }
  } else if (preFormatter === FormatterOpts.BLACK) {
    const blackFormatter = 'ms-python.black-formatter';
    if (vscode.extensions.getExtension(blackFormatter) === undefined) {
      vscode.window.showWarningMessage(
        'Skipping pre-format stage: Black formatter extension not installed',
      );
      logger?.warn(`${blackFormatter} not installed. Skip pre-format`);
    } else {
      // workaround since black doesn't expose an easy command
      const config = vscode.workspace.getConfiguration('editor', {
        languageId: 'python',
      });
      const defaultFormatter: string | undefined =
        config.get('defaultFormatter');
      // change python formatter to black temporarily and format doc
      logger?.info(
        `change python formatter to ${blackFormatter} (current: ${defaultFormatter}) and format doc`,
      );
      await config.update(
        'defaultFormatter',
        blackFormatter,
        vscode.ConfigurationTarget.Workspace,
        true,
      );
      await vscode.commands.executeCommand('editor.action.formatDocument');
      // put default formatter back
      await config.update(
        'defaultFormatter',
        defaultFormatter,
        vscode.ConfigurationTarget.Workspace,
        true,
      );
    }
  }
}

let logger: vscode.LogOutputChannel | undefined;
export function activate(context: vscode.ExtensionContext) {
  logger = vscode.window.createOutputChannel('string-fixer', { log: true });
  context.subscriptions.push({
    dispose: () => {
      logger = undefined;
    },
  });

  let disposable = vscode.commands.registerCommand(
    'string-fixer.run',
    async (file?: string) => {
      const args = file ? ['-t', file] : [];
      const result = await runStringFixer(args);
      if (result?.stderr) {
        const msg = `Error when running string-fixer: ${result.stderr}`;
        logger?.error(msg);
        vscode.window.showErrorMessage(msg);
      }
    },
  );
  context.subscriptions.push(disposable);

  vscode.languages.registerDocumentFormattingEditProvider('python', {
    async provideDocumentFormattingEdits(
      document: vscode.TextDocument,
    ): Promise<undefined> {
      await runPreFormatter();
      await new Promise((r) => setTimeout(r, 100));
      // save doc before running so that process can read the current file version
      await document.save();
      // I tried submitting TextEdits like you're supposed to but they wouldn't apply
      // if I triggered a formatter first, so I'm taking the easy route and just formatting
      // the document via the CLI
      await vscode.commands.executeCommand(
        'string-fixer.run',
        document.fileName,
      );
    },
  });
}

// This method is called when your extension is deactivated
export function deactivate() {}
