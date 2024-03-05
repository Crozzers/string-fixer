import * as vscode from 'vscode';
import * as childProcess from 'child_process';
import { PythonExtension } from '@vscode/python-extension';

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

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand(
    'string-fixer.run',
    async () => {
      let execFolder: string;
      let python: string;
      try {
        execFolder = getExecFolder();
        python = await getPythonExe();
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'There was an unidentified error';
        vscode.window.showErrorMessage(message);
        return;
      }
      // Execute the Python script
      childProcess.execFile(
        python,
        ['-m', 'string-fixer'],
        { cwd: execFolder },
        async (err, stdout, stderr) => {
          if (err) {
            vscode.window.showErrorMessage(`Error: ${err.message}`);
            return;
          }
        },
      );
    },
  );
  context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
