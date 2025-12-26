# Scroll Strategy

Analyze this webpage and determine the BEST way to scroll "{description}".

## Scrollable Elements Found
{scrollable_elements}

## Simplified HTML (first 5000 chars)
{simplified_html}

## Instructions

Determine the scrolling strategy. Return:

1. **method**: Choose one of:
   - "window" - scroll the whole page
   - "element" - scroll a specific element
   - "container" - scroll a container div

2. **selector**: CSS selector for the scrollable element (if method is element/container)

3. **javascript**: Complete IIFE JavaScript code to scroll, like:
```javascript
(() => {
  const el = document.querySelector('.selector');
  if (el) el.scrollTop += 1000;
  return {success: true, scrolled: el.scrollTop};
})()
```

4. **explanation**: Why this method will work

User wants to scroll: "{description}"
