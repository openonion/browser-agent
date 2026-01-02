/**
 * Extract interactive elements from the page with injected IDs.
 * 
 * Works inside individual frames.
 */
(startIndex = 0) => {
    const results = [];
    let index = startIndex;

    const INTERACTIVE_TAGS = new Set([
        'a', 'button', 'input', 'select', 'textarea', 'label',
        'details', 'summary', 'dialog'
    ]);

    const INTERACTIVE_ROLES = new Set([
        'button', 'link', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
        'option', 'radio', 'switch', 'tab', 'checkbox', 'textbox',
        'searchbox', 'combobox', 'listbox', 'slider', 'spinbutton'
    ]);

    function isVisible(el) {
        const style = window.getComputedStyle(el);
        if (style.display === 'none') return false;
        if (style.visibility === 'hidden') return false;
        if (parseFloat(style.opacity) === 0) return false;

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;

        return true;
    }

    function getText(el) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            return el.value || el.placeholder || '';
        }
        return (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').substring(0, 80);
    }

    document.querySelectorAll('*').forEach(el => {
        const tag = el.tagName.toLowerCase();
        const role = el.getAttribute('role');

        const isInteractive = INTERACTIVE_TAGS.has(tag) || 
                            (role && INTERACTIVE_ROLES.has(role)) ||
                            window.getComputedStyle(el).cursor === 'pointer' ||
                            (el.hasAttribute('tabindex') && el.tabIndex >= 0);

        if (!isInteractive || (tag === 'input' && el.type === 'hidden')) return;
        if (!isVisible(el)) return;

        const text = getText(el);
        if (!text && !el.getAttribute('aria-label') && !el.placeholder && tag !== 'input') return;

        const highlightId = String(index);
        el.setAttribute('data-browser-agent-id', highlightId);
        const rect = el.getBoundingClientRect();

        results.append({
            index: index++,
            tag: tag,
            text: text,
            role: role,
            aria_label: el.getAttribute('aria-label'),
            placeholder: el.placeholder || null,
            input_type: el.type || null,
            href: (tag === 'a' && el.href) ? el.href.substring(0, 100) : null,
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
            locator: `[data-browser-agent-id="${highlightId}"]`
        });
    });

    return results;
}
