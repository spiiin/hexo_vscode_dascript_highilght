import * as vscode from 'vscode';
import express from 'express';
import bodyParser from 'body-parser';

const cp = require('child_process');

export function activate(context: vscode.ExtensionContext) {
	let disposable = vscode.commands.registerCommand('spiiin.highlightSource', () => {
		startServer();
		vscode.window.showInformationMessage('Highlight server started!');
	});
	context.subscriptions.push(disposable);
}

export function deactivate() {}

function getActiveFileContent(): string | null {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		return null;
	}
	const document = editor.document;
	return document.getText();
}

function replaceActiveFileContent(newContent: string): boolean {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		return false;
	}
	const document = editor.document;
	const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length));
	editor.edit(editBuilder => {
		editBuilder.replace(fullRange, newContent);
	});
	return true;
}

function copyToClipboard(): void {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		return;
	}
	const document = editor.document;
	const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length));
	editor.selection = new vscode.Selection(fullRange.start, fullRange.end);
	vscode.commands.executeCommand('editor.action.clipboardCopyAction');
}

//copy-paste from d3v.pastespecial, but without vscode.window.showQuickPick (it waits while user selects option, can't be used in script mode)
function getClipboardData(callback:(text:string) => void)
{
	const ext = vscode.extensions.getExtension('d3v.pastespecial');
	if (!ext) {
		return ""; //no extension d3v.pastespecial found
	}
	let cmd = "";
	if (process.platform === "win32") {
		cmd = ext.extensionPath + "\\bin\\win32\\winclip.exe";
	} else if (process.platform === "linux") {
		cmd = ext.extensionPath + "/bin/linux/gtkclip";
	} else {
		vscode.env.clipboard.readText().then((text) => {
			callback(text);
		});
		return;
	}

	cp.exec(cmd, async (err : Error, stdout : string, stderr : string) => {
		if (err) {
			console.log("error '" + err + "' when executing command '" + cmd + "'");
		} else {
			const obj = JSON.parse(stdout);
			if (Array.isArray(obj)) {
				let pickName = new Array();
				let pickFormat = new Array();
				for (let index = 0; index < obj.length; index++) { 
					pickName.push(obj[index].name);
					pickFormat.push(obj[index].format);
				} 
				const index = 1; //Select "Paste HTML source"
				const format = pickFormat[index];
				cp.exec(cmd + " " + format, async (err:Error, stdout:string, stderr:string) => {
					if (err) {
						console.error(err);
					} else {
						const obj = JSON.parse(stdout);
						callback(obj.data);
					}
				});
			}
		}
	});
}

function pasteSpecial(res : express.Response)
{
	const editor = vscode.window.activeTextEditor;
	if (editor) {
		const document = editor.document;
		getClipboardData((text:string) => {
			editor.edit(editBuilder => {
				const fullRange = new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length));
				editor.selection = new vscode.Selection(fullRange.start, fullRange.end);
				editor.selections.forEach(sel => {
					const range = sel.isEmpty ? document.getWordRangeAtPosition(sel.start) || sel : sel;
					editBuilder.replace(range, text);
					res.send({ status: 'success', message: text });
				});
			});
		});
	}
}

function executeSequence(res : express.Response): void 
{
	copyToClipboard();
	setTimeout(() => {
		pasteSpecial(res);
		//vscode.commands.executeCommand('editor.action.clipboardPasteAction');
	}, 500);
}

function startServer() {
	const app = express();
	const PORT = 3000;

	app.use(bodyParser.json());
	app.use(bodyParser.urlencoded({ extended: true }));

	app.post('/', (req, res) => {
		let newFileContent = req.body.fileContent;
		if (newFileContent) {
			replaceActiveFileContent(newFileContent);
			setTimeout(() => {
				executeSequence(res);
			}, 500);
		} else {
			res.send({ status: 'error', message: '' });
		}
	});

	app.listen(PORT, () => {
		console.log(`Highlight server started on http://localhost:${PORT}`);
	});
}