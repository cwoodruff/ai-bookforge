-- Render ```mermaid code blocks to PNG with mermaid-cli (mmdc), cached by content hash in build/diagrams/.
-- A render failure stops the build, so diagram source never leaks into a published book.
local outdir = "build/diagrams"
local mmdc = os.getenv("MMDC") or "mmdc"
local pconf = os.getenv("PUPPETEER_CONFIG")
os.execute("mkdir -p " .. outdir)

local sha1 = (pandoc.utils and pandoc.utils.sha1) or pandoc.sha1

local function exists(p) local f = io.open(p, "r"); if f then f:close(); return true end; return false end

function CodeBlock(el)
  if not el.classes:includes("mermaid") then return nil end
  local hash = sha1(el.text)
  local png = outdir .. "/" .. hash .. ".png"
  if not exists(png) then
    local src = outdir .. "/" .. hash .. ".mmd"
    local f = io.open(src, "w"); f:write(el.text); f:close()
    local cfg = (pconf and exists(pconf)) and (" -p '" .. pconf .. "'") or ""
    local ok = os.execute(mmdc .. cfg .. " -q -b white -s 2 -i " .. src .. " -o " .. png .. " >/dev/null 2>&1")
    if not ok or not exists(png) then
      error("Mermaid render failed for " .. src .. "; fix the diagram (try: mmdc -i " .. src .. " -o /tmp/x.png)")
    end
  end
  local caption = el.attributes["caption"] or ""
  return pandoc.Para({ pandoc.Image(caption, png, "", pandoc.Attr("", {"diagram"}, {})) })
end
