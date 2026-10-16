data = """
hehe: "{{ wat }}"
wet: "{{ omag }}"
---
{{ #if isCool }}
canEnter: true
{{ #if isReallyCool }}
canAllHaveFun:true
{{ end }}
{{ end }}
---
users:
{{ #foreach users }}
  - name: {{ name }}
    email: {{ email }}
{{ #if isReallyCool }}
    canHaveFun: true
{{ #foreach friends }}  
    {{ id }}: true
{{ end }}
{{ end }}
{{ end }}
---
hmm: "hee"
"""

multiline_block_prefixes = [
  "{{ #foreach ", "{{ #if "
]

def template_string_to_ast(template_str):
  blocks = []

  currentIdx = 0

  def proceed_until_end_of_line():
    nonlocal currentIdx

    while not template_str[currentIdx] != '\n':
      currentIdx += 1

  def proceed_until_end_of_multiline_block():
    nonlocal currentIdx

    multiline_inside_block_detected_count = 0
    while True:
      if template_str.startswith("{{ end }}", currentIdx):
        if multiline_inside_block_detected_count == 0:
          break
        multiline_inside_block_detected_count -= 1
        # print("dec!")

      for mb in multiline_block_prefixes:
        if template_str.startswith(mb, currentIdx):
          # print("inc!")
          multiline_inside_block_detected_count += 1
      
      currentIdx += 1
      # print(currentIdx, template_str[currentIdx:currentIdx+10])
  
  while True:
    if currentIdx >= len(template_str) - 1:
      break

    if template_str.startswith("{{ #foreach ", currentIdx):
      currentBlock = { "type": "foreach", "pos_start": currentIdx }
      currentIdx += len("{{ #foreach ")

      proceed_until_end_of_multiline_block()

      currentIdx += len("{{ end }}")
      currentBlock["pos_end"] = currentIdx
      blocks.append(currentBlock)

      continue

    if template_str.startswith("{{ #if ", currentIdx):
      currentBlock = { "type": "if", "pos_start": currentIdx }
      currentIdx += len("{{ #if ")

      proceed_until_end_of_multiline_block()

      currentIdx += len("{{ end }}")
      currentBlock["pos_end"] = currentIdx
      blocks.append(currentBlock)

      continue

    if template_str.startswith("{{", currentIdx):
      currentBlock = { "type": "variable", "pos_start": currentIdx }
      currentIdx += len("{{")

      while not template_str.startswith("}}", currentIdx):
        currentIdx+=1

      currentIdx += len("}}")

      currentBlock["pos_end"] = currentIdx
      currentBlock["content"] = template_str[currentBlock["pos_start"]+len("{{"):currentBlock["pos_end"]-len("}}")]
      
      blocks.append(currentBlock)

      continue
    
    currentIdx += 1

  return blocks

def ast_blocks_to_rendered_template(template_str, blocks, inputDataContext):
  parsed_template_chunks = []
  last_pos_end = 0

  def find_current_line_range(idx):
    nonlocal template_str

    previous_line_end = str(template_str).rfind('\n', 0, idx)
    current_line_end = str(template_str).find('\n', idx)

    if previous_line_end == -1:
      previous_line_end = 0

    if current_line_end == -1:
      current_line_end = len(template_str) - 1

    return previous_line_end + 1, current_line_end
    

  for block in blocks:
    template_chunk = template_str[last_pos_end:block["pos_start"]]
    parsed_template_chunks.append(template_chunk)
    ###
    
    parsed_block_result = "<todo: block result>"

    if block["type"] == "variable":
      var_name = str(block["content"]).strip()
      if var_name in inputDataContext:
        parsed_block_result = inputDataContext[var_name]
      else:
        parsed_block_result = ""

      parsed_template_chunks.append(parsed_block_result)

    if block["type"] == "if":
      pos_end = template_str.index("}}", block["pos_start"])

      var_name = str(template_str[block["pos_start"] + len("{{ #if "):pos_end]).strip()
      block_end_start = block["pos_end"] - len("{{ end }}")

      template_line_start, template_line_end = find_current_line_range(block["pos_start"])
      template_line_content = template_str[template_line_start:template_line_end]

      end_line_start, end_line_end = find_current_line_range(block["pos_end"])
      end_line_content = template_str[end_line_start:end_line_end]

      print("template line start")
      print(f"[{template_line_content}]")
      print(f"[{end_line_content}]")
      print("template line end")

      if var_name in inputDataContext and inputDataContext[var_name] != "false":
        block_template = template_str[pos_end+len("}}"):block_end_start]

        block_template_ast = template_string_to_ast(block_template)
        render_result = ast_blocks_to_rendered_template(block_template, block_template_ast, inputDataContext)
        render_result = str(render_result).removeprefix("\n")
        render_result = str(render_result).removesuffix("\n")
        parsed_block_result = render_result
      else:
        parsed_block_result = ""

      parsed_template_chunks.append(parsed_block_result)
      

    if block["type"] == "foreach":
      pos_end = template_str.index("}}", block["pos_start"])

      var_name = str(template_str[block["pos_start"] + len("{{ #foreach "):pos_end]).strip()
      block_end_start = block["pos_end"]

      block_template = template_str[pos_end+len("}}"):block_end_start]
      block_template = block_template.removeprefix("\n")
      block_template = block_template.removesuffix("\n")

      if var_name in inputDataContext:
        parsed_block_result = ""

        for it in inputDataContext[var_name]:
          block_template_ast = template_string_to_ast(block_template)
          render_result = ast_blocks_to_rendered_template(block_template, block_template_ast, it)
          parsed_template_chunks.append(render_result)

      else:
        parsed_block_result = ""

      pass

    
    ###
    last_pos_end = block["pos_end"]

  # print(json.dumps(parsed_template_chunks))

  if len(blocks) == 0:
    parsed_template_chunks.append(template_str)
  else:
    parsed_template_chunks.append(template_str[last_pos_end:])

  result = "".join(parsed_template_chunks)

  return result



def main():
  blocks = template_string_to_ast(data)

  # print(json.dumps(blocks))

  inputDataContext = {
    "wat": "wat_result",
    "omag": "omag_result",
    "isCool": "",
    "isReallyCool": "true",
    "users": [
      { "name": "user_one", "email": "email1@haha.com", "isReallyCool": "true" , "friends": [ { "id": "haha" }, { "id": "hehe" } ]},
      { "name": "user_two", "email": "email2@haha.com" },
    ]
  }

  res = ast_blocks_to_rendered_template(data, blocks, inputDataContext)

  print("-----------------------------------------")
  print(res)
  print("-----------------------------------------")


if __name__ == "__main__":
  main()



