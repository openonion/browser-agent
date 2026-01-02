"""
Element Finder - Find interactive elements by natural language description.
Handles multiple iframes.
"""

from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field
from connectonion import llm_do


# Load JavaScript and prompt from files
_BASE_DIR = Path(__file__).parent
_EXTRACT_JS = (_BASE_DIR / "scripts" / "extract_elements.js").read_text()
_ELEMENT_MATCHER_PROMPT = (_BASE_DIR.parent / "prompts" / "element_matcher.md").read_text()


class InteractiveElement(BaseModel):
    """An interactive element on the page with pre-built locator."""
    index: int
    tag: str
    text: str = ""
    role: Optional[str] = None
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    input_type: Optional[str] = None
    href: Optional[str] = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    locator: str = ""
    frame_index: int = 0 # 0 is main frame


class ElementMatch(BaseModel):
    """LLM's element selection result."""
    index: int = Field(..., description="Index of the matching element")
    confidence: float = Field(..., description="Confidence 0-1")
    reasoning: str = Field(..., description="Why this element matches")


def extract_elements(page) -> List[InteractiveElement]:
    """Extract all interactive elements from the page including iframes."""
    all_elements = []
    current_index = 0
    
    for i, frame in enumerate(page.frames):
        try:
            # Run extraction in this frame
            raw_elements = frame.evaluate(_EXTRACT_JS, current_index)
            
            # If in a subframe, adjust coordinates based on iframe position
            offset_x, offset_y = 0, 0
            if i > 0: # Not main frame
                try:
                    frame_element = frame.frame_element()
                    if frame_element:
                        box = frame_element.bounding_box()
                        if box:
                            offset_x, offset_y = box['x'], box['y']
                except:
                    pass # Cross-origin might prevent frame_element access
            
            for el_data in raw_elements:
                el = InteractiveElement(**el_data)
                el.frame_index = i
                el.x += int(offset_x)
                el.y += int(offset_y)
                all_elements.append(el)
                current_index += 1
        except:
            continue # Skip frames that are inaccessible or broken
            
    return all_elements


def format_elements_for_llm(elements: List[InteractiveElement], max_count: int = 150) -> str:
    """Format elements as compact list for LLM context."""
    lines = []
    for el in elements[:max_count]:
        parts = [f"[{el.index}]", el.tag]

        if el.text:
            parts.append(f'"{el.text}"')
        elif el.placeholder:
            parts.append(f'placeholder="{el.placeholder}"')
        elif el.aria_label:
            parts.append(f'aria="{el.aria_label}"')

        parts.append(f"pos=({el.x},{el.y})")
        if el.frame_index > 0:
            parts.append(f"(in iframe)")

        lines.append(' '.join(parts))

    return '\n'.join(lines)


def find_element(
    page,
    description: str,
    elements: List[InteractiveElement] = None
) -> Optional[InteractiveElement]:
    """Find an interactive element by natural language description."""
    if elements is None:
        elements = extract_elements(page)

    if not elements:
        return None

    element_list = format_elements_for_llm(elements)

    prompt = _ELEMENT_MATCHER_PROMPT.format(
        description=description,
        element_list=element_list
    )

    result = llm_do(
        prompt,
        output=ElementMatch,
        model="co/gemini-2.5-flash",
        temperature=0.1
    )

    if 0 <= result.index < len(elements):
        return elements[result.index]

    return None