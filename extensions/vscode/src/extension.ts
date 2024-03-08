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
  // Execute the Python script
  return execFile(python, ['-m', 'string-fixer'].concat(...(cmdArgs || [])), {
    cwd: execFolder,
  });
}

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand(
    'string-fixer.run',
    async () => {
      const result = await runStringFixer();
      if (result?.stderr) {
        vscode.window.showErrorMessage(`Error: ${stderr}`);
        return;
      }
    },
  );
  context.subscriptions.push(disposable);

  vscode.languages.registerDocumentFormattingEditProvider('python', {
    async provideDocumentFormattingEdits(
      document: vscode.TextDocument,
    ): Promise<vscode.TextEdit[]> {
      // save doc before running so that process can read the current file version
      await document.save();
      const tweaks: vscode.TextEdit[] = [];

      const result = await runStringFixer(['-d', '-t', document.fileName]);

      if (result?.stderr) {
        let index = -1;
        for (const line of result?.stderr.split('\n')) {
          index++;
          if (!line.length) {
            continue;
          }
          const current = document.lineAt(index);
          if (line !== current.text) {
            tweaks.push(vscode.TextEdit.replace(current.range, line));
          }
        }
      }
      return tweaks;
    },
  });
}

// This method is called when your extension is deactivated
export function deactivate() {}
