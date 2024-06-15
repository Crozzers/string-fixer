import * as vscode from 'vscode';
import * as childProcess from 'child_process';
import { PythonExtension } from '@vscode/python-extension';
import { promisify } from 'util';
import * as path from 'path';

const execFile = promisify(childProcess.execFile);

function isParent(parent: string, child: string) {
  // https://stackoverflow.com/a/45242825
  const relative = path.relative(parent, child);
  return relative && !relative.startsWith('..') && !path.isAbsolute(relative);
}

function getExecFolder(): string {
  // get parent folder of current open doc
  let activeFolder: string | null = null;
  if (vscode.window.activeTextEditor) {
    activeFolder = path.join(
      vscode.window.activeTextEditor.document.uri.path,
      '..',
    );
  }
  // get all active workspaces and filter by which ones contain the currently active file (if applicable)
  let workspaces: vscode.WorkspaceFolder[] = [];
  if (vscode.workspace.workspaceFolders) {
    workspaces = vscode.workspace.workspaceFolders.slice();
    if (activeFolder) {
      workspaces = workspaces.filter((f) => isParent(f.uri.path, activeFolder));
    }
  }

  if (workspaces.length === 0) {
    if (activeFolder) {
      return activeFolder;
    }
    throw new Error('no workspace or open files detected');
  }

  const workspace = workspaces[0];
  const config = vscode.workspace.getConfiguration('string-fixer', workspace);
  const folder: string | undefined = config.get('folder');
  // do this rather than `config.has` because typescript compiler
  if (folder) {
    return path.join(workspace.uri.fsPath, folder);
  }
  return workspace.uri.fsPath;
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
  const args = ['-m', 'string_fixer'].concat(...(cmdArgs || []));
  logger?.info(`running string-fixer with args: ${args}`);
  logger?.info(`pythonExe:`, python);
  logger?.info(`execFolder:`, execFolder);
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
