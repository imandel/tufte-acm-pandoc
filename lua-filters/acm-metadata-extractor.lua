-- Automatically extracts ACM conference metadata from LaTeX source

local conference_info = {}


local function extract_conference_info(text)
  if not text then return false end
  
  local found_something = false
  

  local short_name, full_name, dates, location = text:match("\\acmConference%[([^%]]+)%]%{([^}]+)%}%{([^}]+)%}%{([^}]+)%}")
  if short_name and full_name and dates and location then
    conference_info.short_name = short_name
    conference_info.full_name = full_name
    conference_info.dates = dates
    conference_info.location = location
    conference_info.full_citation = full_name .. " (" .. short_name .. "), " .. dates .. ", " .. location
    found_something = true
  end
  
  -- Extract DOI
  local doi = text:match("\\acmDOI%{([^}]+)%}")
  if doi then
    conference_info.doi = doi
    found_something = true
  end
  
  -- Extract year
  local year = text:match("\\acmYear%{(%d+)%}")
  if year then
    conference_info.year = year
    found_something = true
  end
  
  -- Extract copyright year
  local copyright_year = text:match("\\copyrightyear%{(%d+)%}")
  if copyright_year then
    conference_info.copyright_year = copyright_year
    found_something = true
  end
  
  -- Extract book title (full conference citation)
  local book_title = text:match("\\acmBooktitle%{([^}]+)%}")
  if book_title then
    conference_info.book_title = book_title
    found_something = true
  end
  
  return found_something
end

-- Check RawBlock elements
function RawBlock(elem)
  if elem.format == "latex" then
    extract_conference_info(elem.text)
  end
  return elem
end

-- Check RawInline elements  
function RawInline(elem)
  if elem.format == "latex" then
    extract_conference_info(elem.text)
  end
  return elem
end

function Pandoc(doc)
  -- Try to read from the main LaTeX file if we haven't found info yet
  if next(conference_info) == nil then
    local f = io.open("00_main.tex", "r")
    if f then
      local content = f:read("*all")
      f:close()
      extract_conference_info(content)
    end
  end
  
  -- Set metadata variables that can be used in templates
  if conference_info.full_citation then
    doc.meta.conference = pandoc.MetaString(conference_info.full_citation)
  elseif conference_info.book_title then
    doc.meta.conference = pandoc.MetaString(conference_info.book_title)
  end
  
  if conference_info.doi then
    doc.meta.doi = pandoc.MetaString(conference_info.doi)
  end
  
  if conference_info.year then
    doc.meta.conference_year = pandoc.MetaString(conference_info.year)
  end
  
  -- Create conference info block if we have information
  if next(conference_info) ~= nil then
    -- Create margin note content
    local margin_content = {}
    
    -- Add conference citation
    if conference_info.full_citation then
      table.insert(margin_content, pandoc.Str(conference_info.full_citation))
      table.insert(margin_content, pandoc.LineBreak())
      table.insert(margin_content, pandoc.LineBreak())
    elseif conference_info.book_title then
      table.insert(margin_content, pandoc.Str(conference_info.book_title))
      table.insert(margin_content, pandoc.LineBreak())
      table.insert(margin_content, pandoc.LineBreak())
    end
    
    -- Add DOI
    if conference_info.doi then
      table.insert(margin_content, pandoc.Str("DOI: "))
      local doi_link = pandoc.Link(conference_info.doi, "https://doi.org/" .. conference_info.doi)
      table.insert(margin_content, doi_link)
      table.insert(margin_content, pandoc.LineBreak())
    end
    
    -- Create the margin note span
    local margin_note = pandoc.Span(margin_content, {class = "marginnote"})
    
    -- Attach the margin note to the teaser figure (Block 2) or first paragraph
    io.stderr:write("DEBUG: Looking for teaser figure or first paragraph\n")
    
    local attached = false
    for i, block in ipairs(doc.blocks) do
      -- Try to attach to teaserfigure div first
      if not attached and block.tag == "Div" and block.classes and 
         block.classes:includes("teaserfigure") then
        io.stderr:write("DEBUG: Found teaserfigure div at block " .. i .. "\n")
        -- Find the first element we can attach to in the teaser
        for j, elem in ipairs(block.content) do
          if elem.tag == "Para" then
            io.stderr:write("DEBUG: Attaching margin note to teaserfigure paragraph\n")
            table.insert(elem.content, 1, margin_note)
            attached = true
            break
          end
        end
        -- If no paragraph in teaser, create one
        if not attached then
          io.stderr:write("DEBUG: No paragraph in teaserfigure, creating one\n")
          local margin_para = pandoc.Para({margin_note})
          table.insert(block.content, 1, margin_para)
          attached = true
        end
        break
      end
    end
    
    -- Fallback to first paragraph if teaser approach didn't work
    if not attached then
      io.stderr:write("DEBUG: No teaserfigure found, attaching to first paragraph\n")
      for i, block in ipairs(doc.blocks) do
        if block.tag == "Para" then
          io.stderr:write("DEBUG: Found first paragraph at block " .. i .. ", attaching margin note\n")
          table.insert(block.content, 1, margin_note)
          attached = true
          break
        end
      end
    end
  end
  
  return doc
end