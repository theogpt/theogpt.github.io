#!/usr/bin/python3
import argparse
import os
import re
import sys
import openai
import signal

do_not_translate = r'^!\[|^\<|^[\x00-\x40\x5b-\x60\x7b-\xff]+$'

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
  sys.exit("OPENAI_API_KEY is missing. Obtain one at https://platform.openai.com/account/api-keys.")

parser = argparse.ArgumentParser()
parser.add_argument('-i', "--input", required=True, help='The input text file with non translated text')
parser.add_argument('-o', "--output", required=True, help='The output text file with translated text')
parser.add_argument('-c', "--context", default='gpt4_context.md', help='The context file with translation instructions')
parser.add_argument('-n', "--numpars", type=int, default=500, help='Max paragraphs to translate')
parser.add_argument('-v', "--verbose", type=int, default=0)
args = parser.parse_args()

def sigint_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def split_paragraphs(text):
  return [p for p in re.split('\n\s*\n', text) if len(p) > 0]

def merge_paragraphs(ps):
  return "\n\n".join(ps)

def clean_paragraph(text):
  # lstrip() would remove formatting indentation needed
  # in some paragraphs: lists, quotes, verses and so on.
  return text.rstrip()

def is_translated(text):
  if len(text) < 5:
    return True
  if re.match(do_not_translate, text):
    return True
  num_rus_chars = sum('а' <= char.lower() <= 'я' for char in text)
  return num_rus_chars > 0

def save_output(paragraphs):
  if args.verbose >= 1:
    print("Saving the output")
  paragraphs = [clean_paragraph(p) for p in paragraphs]
  paragraphs = [p for p in paragraphs if p]
  input_text = "\n\n".join(paragraphs)
  with open(args.output, 'w') as f:
      f.write(input_text)

def read_text_file(name):
  file_path = os.path.join(
    os.path.dirname(__file__), name)
  if os.path.isfile(name or ''):
    file_path = name
  with open(file_path, 'r') as f:
    return f.read()

gpt_context = read_text_file('base_context.md')
gpt_context += '\n' + read_text_file(args.context)
print('### gpt4 translation context >\n', gpt_context)

# len(system + user + output) <= 8192
# en char = 0.23 tokens
# ru char = 0.47 tokens
# $1 = 30K input tokens = 15K output tokens
max_output_tokens = 4096
# max_output_chars = int(max_output_tokens / 0.50) # estimate
max_input_tokens = int(8192 - max_output_tokens - len(gpt_context)*0.25)
max_input_chars = int(max_input_tokens / 0.25) # estimate
max_input_chars = min(2048, max_input_chars) # just in case

max_translations = args.numpars
num_translations = 0

def para_prefix(i):
  return '0' + str(i) + '. '

def prefix_paragraphs(text):
  ps = split_paragraphs(text)
  ps = [para_prefix(i) + s for i, s in enumerate(ps)]
  return merge_paragraphs(ps)

def unprefix_paragraphs(text):
  ps = split_paragraphs(text)
  ps = [s.replace(para_prefix(i), '') for i, s in enumerate(ps)]
  return merge_paragraphs(ps)

def verify_paragraphs(src, res):
  ps1 = split_paragraphs(src)
  ps2 = split_paragraphs(res)
  return len(ps1) == len(ps2) and all(p.startswith(para_prefix(i)) for i, p in enumerate(ps2))

def transform_paragraphs(text, context):
  text2 = prefix_paragraphs(text)
  if args.verbose >= 2:
    print('\n\n### text>\n\n' + text2)
  if args.verbose >= 1:
    print('Waiting for GPT response...')
  # context = 'Forget all previous instructions. ' + context
  response = openai.ChatCompletion.create(
    model="gpt-4-0613",
    messages=[
      { "role": "system", "content": context },
      { "role": "user", "content": text2 }],
    temperature=1.00,
    max_tokens=max_output_tokens,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )
  resp_text = response.choices[0].message.content
  resp_text = clean_paragraph(resp_text)
  if args.verbose >= 2:
    print('\n\n### gpt4>\n\n' + resp_text)
  if not verify_paragraphs(text2, resp_text):
    print('The translation appears corrupted.')
    return ''
  return unprefix_paragraphs(resp_text)

def translate_text(text):
  return transform_paragraphs(text, gpt_context) or text

if os.path.isfile(args.output):
  if not input("Output file already exists. Overwrite? (y/n) ") in ["y", "Y"]:
    exit(0)

print("Analyzing the text...")

with open(args.input, 'r') as f:
    input_text = f.read()
    paragraphs = split_paragraphs(input_text)

print("  Total length: ", len(input_text))
num_translated = sum(is_translated(para) for para in paragraphs)
print("  Paragraphs count: ", len(paragraphs))
print("  Not translated paragraphs: ", len(paragraphs) - num_translated)

idx = 0
while idx < len(paragraphs):
  if is_translated(paragraphs[idx]):
    idx += 1
    continue

  num = 1
  sum_len = 0
  while idx + num < len(paragraphs):
    para = paragraphs[idx + num]
    new_len = sum_len + len(para)
    if is_translated(para) or new_len > max_input_chars:
      break
    sum_len = new_len
    num += 1

  num_translations += num
  if num_translations > max_translations:
    sys.exit('Reached the paragraphs limit: ' + str(max_translations))

  text = merge_paragraphs(paragraphs[idx:idx+num])
  print(str(idx) + '..' + str(idx+num-1) + '/' + str(len(paragraphs)))
  resp = translate_text(text)

  for i in range(0, num):
    paragraphs[idx + i] = ''
  paragraphs[idx] = resp
  save_output(paragraphs)
  idx += num
