import re, hashlib, requests, json, time, os

BASE_PATH = "d:/src/hexo/hexo/blog/"

SOURCE_PATH = os.path.join(BASE_PATH, "source/_posts/")
OUT_PATH_TEMPLATE = os.path.join(BASE_PATH, "public/blog/%s/index.html")
CACHE_NAME = "highlights_hashes.txt"

PROCESS_FNAMES = [
	"230919-dascript-bgfx-wbiot.md",
	"230905-dascript-bindings-tricks.md",
	"230308-dascript-contexts.md",
	"230305-dascript-small-things.md",
	"230101-dascript-in-gamedev.md",
	"221225-dascript-soft-render.md",
	"221111-dascript-brainfuck.md",
	"221022-dascript-sfml-blend.md",
	"221105-dascript-sfml-spines.md",
	"220904-iterators-2.md",
	"220731-iterators.md",
	"220727-dascript-fast.md",
	"220702-dascript-macro2.md",
	"220626-dascript-how-to-learn.md",
	"220619-dascript-in-imaginery-world.md",
	"220618-dascript-live.md",
	"220612-dascript-interview.md",
	"220612-dascript-assimp.md",
	"220530-dascript-bindings.md",
	"220223-dascript-links.md",
	"220220-dascript-gl.md",
	"220206-dascript-macro.md",
	"220130-about-cpp-gamedev.md",
	"231014-vm.md",
	"231016-dascript-examples.md",
	"230112-dascript-oop.md",
	"230121-dascript-generics.md"
]

url = "http://localhost:3000" #address of server

def find_code_snippets(filename):
	with open(filename, 'rt', encoding='utf-8') as file:
		content = file.read()
		pattern = r'```fsharp(.*?)```'
		snippets = re.findall(pattern, content, re.DOTALL)
		return [snippet.strip() for snippet in snippets]
		
def extract_abbrlink(filename):
	with open(filename, 'r', encoding='utf-8') as file:
		content = file.read()
	pattern = r'abbrlink:\s*(\d+)'
	match = re.search(pattern, content)
	if match:
		return match.group(1)
	else:
		return None

def compute_sha256(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()

def debug_print_snippets(snippets):
	for index, snippet in enumerate(snippets, 1):
		print(f"-------- {index} --------")
		print("```fsharp") #we need to use some existing language, because hexo default highlighter need it
		print(f"\n{snippet}\n")
		print("```")

def request_to_vs_code(text):
	response = requests.post(url, headers = {"Content-Type": "application/json"}, json = {"fileContent": text})
	return response.text
	
def replace_figure_with_string(filename, hashes, highlight_html):
	with open(filename, 'r', encoding='utf-8') as file:
		content = file.read()
	pattern = r'<figure class="highlight fsharp">.*?</figure>'
	replacements_iter = iter(hashes)
	def replacement_func(match):
		val = next(replacements_iter)
		print(f"  Replaced {val}")
		return highlight_html[val]
	modified_content = re.sub(pattern, replacement_func, content, flags=re.DOTALL)
	with open(filename, 'w', encoding='utf-8') as file:
		file.write(modified_content)

def main():
	highlight_html = {}
	if os.path.exists(CACHE_NAME):
		with open(CACHE_NAME, "rt") as f:
			highlight_html = eval(f.read())

	snippet_hashes = {}
	for process_fname in PROCESS_FNAMES:
		path = os.path.join(SOURCE_PATH, process_fname)
		snippets = find_code_snippets(path)
		hashes = [compute_sha256(snippet) for snippet in snippets]
		print(f"Proccess file: {path}. Found {len(hashes)} code snippets")
		snippet_hashes[path] = hashes

		for snippet, snippet_hash in zip(snippets, hashes):
			print(f"Request: {snippet_hash}")
			if snippet_hash not in highlight_html:
				js = json.loads(request_to_vs_code(snippet))
				highlight_html[snippet_hash] = js["message"]
				time.sleep(0.5)

	with open(CACHE_NAME, "wt") as f:
		f.write(str(highlight_html))
	#debug_print_snippets(snippets)

	print("-"*80)
	for process_fname in PROCESS_FNAMES:
		path = os.path.join(SOURCE_PATH, process_fname)
		abbr_link = extract_abbrlink(path)
		out_path = OUT_PATH_TEMPLATE%(abbr_link)
		print(f"Replace file: {path} ({out_path})")
		input_path = os.path.join(SOURCE_PATH, process_fname)
		replace_figure_with_string(out_path, snippet_hashes[input_path], highlight_html)

main()