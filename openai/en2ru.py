#!/usr/bin/python3
# Avg price to translate a book: $100 per 1 million chars.
import argparse
import os
import re
import sys
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
  sys.exit("OPENAI_API_KEY is missing. Obtain one at https://platform.openai.com/account/api-keys.")

parser = argparse.ArgumentParser()
parser.add_argument('-i', "--input", required=True, help='The input text file with non translated text')
parser.add_argument('-o', "--output", required=True, help='The output text file with translated text')
parser.add_argument('-c', "--context", required=False, help='The context file with translation instructions')
parser.add_argument('-q', "--quality", type=int, default=1, help='The quality of translation')
parser.add_argument('-v', "--verbose", default=False)
args = parser.parse_args()

def is_translated(text):
  if len(text) < 10:
    return True
  if re.match(r'^!\[\]|^#|^\<|^_|^\d+$|^\s*$', text):
    return True
  num_rus_chars = sum('а' <= char.lower() <= 'я' for char in text)
  return num_rus_chars > 0

def save_output(paragraphs):
  print("Saving the output")
  cleaned = filter(lambda s: bool(s), map(lambda s: s.strip(), paragraphs))
  input_text = "\n\n".join(cleaned)
  with open(args.output, 'w') as f:
      f.write(input_text)

if not os.path.isfile(args.context or ''):
  gpt_context = "You are a translator from English to Russian."
else:
  with open(args.context, 'r') as f:
    gpt_context = f.read()

# len(system + user + output) <= 8192
# en char = 0.23 tokens
# ru char = 0.47 tokens
# $1 = 30K input tokens = 15K output tokens
max_output_tokens = 4096
max_output_chars = int(max_output_tokens / 0.50) # estimate
max_input_tokens = int(8192 - max_output_tokens - len(gpt_context)*0.25)
max_input_chars = int(max_input_tokens / 0.25) # estimate
max_input_chars = min(4096, max_input_chars) # just in case

max_translations = 500
num_translations = 0

def translate(text, draft=''):
  global num_translations
  num_translations += 1
  if num_translations > max_translations:
    sys.exit('Reached the translations limit: ' + str(max_translations))

  messages=[
    { "role": "system", "content": gpt_context },
    { "role": "user", "content": text }]
  if draft:
    messages += [{ "role": "user", "content": 'Draft translation:\n' + draft }]

  print('Waiting for GPT response...')
  response = openai.ChatCompletion.create(
    model="gpt-4-0613",
    messages=messages,
    temperature=1.00,
    max_tokens=max_output_tokens,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
  )
  return response.choices[0].message.content

def translate2(text, iterations):
  if iterations > 1:
    print('Translating with', iterations, 'iterations')
  resp = translate(text)
  for i in range(1, iterations):
    resp = translate(text, resp)
  return resp

if os.path.isfile(args.output):
  if not input("Output file already exists. Overwrite? (y/n) ") in ["y", "Y"]:
    exit(0)

print("Analyzing the text...")

with open(args.input, 'r') as f:
    input_text = f.read()
    paragraphs = re.split('\s*\n\s*\n\s*', input_text)

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

  text = "\n\n".join(paragraphs[idx:idx+num])
  print(str(idx) + '..' + str(idx+num-1) + '/' + str(len(paragraphs)))
  if args.verbose:
    print('en> ', text)

  resp = translate2(text, args.quality)
  if args.verbose:
    print('ru>', resp)

  for i in range(0, num):
    paragraphs[idx + i] = ''
  paragraphs[idx] = resp
  save_output(paragraphs)
  idx += num
