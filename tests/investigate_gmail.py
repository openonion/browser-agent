"""
Investigate Gmail's HTML/JS structure to understand why scrolling doesn't work.
Then test ALL possible scrolling methods systematically.
"""

from web_automation import WebAutomation
import time

def investigate_gmail():
    print("=== Investigating Gmail Scrolling Mechanism ===\n")

    web = WebAutomation(use_chrome_profile=True)
    web.open_browser(headless=False)
    web.go_to("https://gmail.com")
    time.sleep(3)

    print("1. Finding all scrollable elements...")
    scrollable_info = web.page.evaluate("""
        (() => {
            const allElements = Array.from(document.querySelectorAll('*'));
            const scrollable = [];

            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const hasOverflow = style.overflow === 'auto' || style.overflow === 'scroll' ||
                                   style.overflowY === 'auto' || style.overflowY === 'scroll';

                if (hasOverflow) {
                    scrollable.push({
                        tag: el.tagName,
                        classes: el.className,
                        id: el.id,
                        role: el.getAttribute('role'),
                        scrollTop: el.scrollTop,
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight,
                        canScroll: el.scrollHeight > el.clientHeight,
                        overflow: style.overflow,
                        overflowY: style.overflowY
                    });
                }
            });

            return scrollable;
        })()
    """)

    print(f"\nFound {len(scrollable_info)} scrollable elements:")
    for i, el in enumerate(scrollable_info):
        print(f"\n  Element {i+1}:")
        print(f"    Tag: {el['tag']}")
        print(f"    Classes: {el['classes']}")
        print(f"    Role: {el['role']}")
        print(f"    ScrollTop: {el['scrollTop']}")
        print(f"    ScrollHeight: {el['scrollHeight']}")
        print(f"    ClientHeight: {el['clientHeight']}")
        print(f"    Can scroll: {el['canScroll']}")
        print(f"    Overflow: {el['overflow']} / {el['overflowY']}")

    print("\n\n2. Finding email list container structure...")
    email_structure = web.page.evaluate("""
        (() => {
            // Find the main email list
            const emailList = document.querySelector('[role="main"]');
            if (!emailList) return {error: "No role=main found"};

            const rows = emailList.querySelectorAll('[role="row"]');

            return {
                mainElement: {
                    tag: emailList.tagName,
                    classes: emailList.className,
                    scrollTop: emailList.scrollTop,
                    scrollHeight: emailList.scrollHeight,
                    clientHeight: emailList.clientHeight,
                    innerHTML_length: emailList.innerHTML.length
                },
                rowCount: rows.length,
                firstRowText: rows[0] ? rows[0].textContent.substring(0, 100) : null,
                lastRowText: rows[rows.length - 1] ? rows[rows.length - 1].textContent.substring(0, 100) : null,
                parentChain: (() => {
                    let chain = [];
                    let current = emailList;
                    while (current.parentElement && chain.length < 10) {
                        current = current.parentElement;
                        const style = window.getComputedStyle(current);
                        chain.push({
                            tag: current.tagName,
                            classes: current.className,
                            overflow: style.overflow,
                            overflowY: style.overflowY,
                            scrollTop: current.scrollTop,
                            scrollHeight: current.scrollHeight,
                            clientHeight: current.clientHeight
                        });
                    }
                    return chain;
                })()
            };
        })()
    """)

    print("\nEmail list structure:")
    print(f"  Main element: {email_structure.get('mainElement')}")
    print(f"  Row count: {email_structure.get('rowCount')}")
    print(f"  First row: {email_structure.get('firstRowText')}")
    print(f"  Last row: {email_structure.get('lastRowText')}")
    print(f"\n  Parent chain (looking for scrollable parent):")
    for i, parent in enumerate(email_structure.get('parentChain', [])):
        print(f"    Level {i+1}: {parent['tag']} - overflow:{parent['overflowY']} scrollTop:{parent['scrollTop']}/{parent['scrollHeight']}")

    print("\n\n3. Checking for event listeners on scroll...")
    event_info = web.page.evaluate("""
        (() => {
            const main = document.querySelector('[role="main"]');
            if (!main) return {error: "No main found"};

            // Try to detect if there are scroll event listeners
            // We can't directly access listeners, but we can test behavior
            return {
                hasOnScroll: main.onscroll !== null,
                hasOnWheel: main.onwheel !== null,
                ariaLabel: main.getAttribute('aria-label'),
                ariaLive: main.getAttribute('aria-live')
            };
        })()
    """)

    print(f"Event listener info: {event_info}")

    print("\n\n4. Taking initial screenshot...")
    web.take_screenshot("investigate_before.png")

    # Now test ALL possible scrolling methods
    print("\n\n=== TESTING ALL SCROLLING METHODS ===\n")

    methods = []

    # Method 0: Scroll the ACTUAL scrollable container we found (.Tm.aeJ)
    print("METHOD 0: Scroll .Tm.aeJ (THE scrollable container)...")
    result0 = web.page.evaluate("""
        (() => {
            const scrollable = document.querySelector('.Tm.aeJ');
            if (!scrollable) return {error: 'Not found'};
            const before = scrollable.scrollTop;
            scrollable.scrollTop += 1000;
            const after = scrollable.scrollTop;
            return {before: before, after: after, delta: after - before};
        })()
    """)
    methods.append(("Scroll .Tm.aeJ", result0))
    time.sleep(2)
    web.take_screenshot("method0_Tm_aeJ.png")

    # Method 1: Scroll window
    print("METHOD 1: Window scrollBy...")
    result1 = web.page.evaluate("(() => { window.scrollBy(0, 1000); return window.scrollY; })()")
    methods.append(("Window scrollBy", result1))
    time.sleep(1)
    web.take_screenshot("method1_window.png")

    # Method 2: Scroll document.documentElement
    print("METHOD 2: Document.documentElement...")
    result2 = web.page.evaluate("""
        (() => {
            document.documentElement.scrollTop += 1000;
            return document.documentElement.scrollTop;
        })()
    """)
    methods.append(("Document.documentElement", result2))
    time.sleep(1)
    web.take_screenshot("method2_documentElement.png")

    # Method 3: Scroll document.body
    print("METHOD 3: Document.body...")
    result3 = web.page.evaluate("""
        (() => {
            document.body.scrollTop += 1000;
            return document.body.scrollTop;
        })()
    """)
    methods.append(("Document.body", result3))
    time.sleep(1)
    web.take_screenshot("method3_body.png")

    # Method 4: Find and scroll the main role
    print("METHOD 4: Role=main element...")
    result4 = web.page.evaluate("""
        const main = document.querySelector('[role="main"]');
        const before = main.scrollTop;
        main.scrollTop += 1000;
        return {before: before, after: main.scrollTop, delta: main.scrollTop - before};
    """)
    methods.append(("Role=main scrollTop", result4))
    time.sleep(1)
    web.take_screenshot("method4_main.png")

    # Method 5: ScrollIntoView on a lower email
    print("METHOD 5: ScrollIntoView on 30th email...")
    result5 = web.page.evaluate("""
        const rows = document.querySelectorAll('[role="row"]');
        if (rows.length > 30) {
            rows[30].scrollIntoView({behavior: 'smooth', block: 'start'});
            return `Scrolled to row 30 of ${rows.length}`;
        }
        return 'Not enough rows';
    """)
    methods.append(("ScrollIntoView", result5))
    time.sleep(2)
    web.take_screenshot("method5_scrollIntoView.png")

    # Method 6: Dispatch scroll event
    print("METHOD 6: Dispatch scroll event...")
    result6 = web.page.evaluate("""
        const main = document.querySelector('[role="main"]');
        const event = new Event('scroll', {bubbles: true});
        main.scrollTop = 1000;
        main.dispatchEvent(event);
        return {scrollTop: main.scrollTop, dispatched: true};
    """)
    methods.append(("Dispatch scroll event", result6))
    time.sleep(1)
    web.take_screenshot("method6_dispatch.png")

    # Method 7: Dispatch wheel event
    print("METHOD 7: Dispatch wheel event...")
    result7 = web.page.evaluate("""
        const main = document.querySelector('[role="main"]');
        const event = new WheelEvent('wheel', {
            deltaY: 1000,
            deltaMode: 0,
            bubbles: true,
            cancelable: true
        });
        main.dispatchEvent(event);
        return {dispatched: true, scrollTop: main.scrollTop};
    """)
    methods.append(("Dispatch wheel event", result7))
    time.sleep(1)
    web.take_screenshot("method7_wheel.png")

    # Method 8: Press 'j' key (Gmail shortcut - next conversation)
    print("METHOD 8: Press 'j' key (next conversation)...")
    web.page.keyboard.press('j')
    time.sleep(0.5)
    web.page.keyboard.press('j')
    time.sleep(0.5)
    web.page.keyboard.press('j')
    methods.append(("Press 'j' key", "Pressed 3 times"))
    time.sleep(1)
    web.take_screenshot("method8_j_key.png")

    # Method 9: Find "Older" button
    print("METHOD 9: Looking for Older/Next button...")
    result9 = web.page.evaluate("""
        const buttons = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
        const older = buttons.find(b => b.textContent.includes('Older') || b.textContent.includes('Next'));
        return older ? {found: true, text: older.textContent, classes: older.className} : {found: false};
    """)
    methods.append(("Find Older button", result9))
    if result9.get('found'):
        print("  Found Older button! Clicking...")
        web.click_element_by_text("Older")
        time.sleep(2)
    web.take_screenshot("method9_older_button.png")

    # Method 10: Change the page URL to show more emails
    print("METHOD 10: Try loading page 2 via URL...")
    current_url = web.page.url
    # Gmail uses fragment navigation
    web.page.evaluate("window.location.hash = '#inbox/p2';")
    time.sleep(2)
    methods.append(("URL fragment p2", web.page.url))
    web.take_screenshot("method10_url_p2.png")

    # Method 11: Press End key
    print("METHOD 11: Press End key...")
    web.page.keyboard.press('End')
    time.sleep(1)
    methods.append(("Press End key", "Pressed"))
    web.take_screenshot("method11_end_key.png")

    # Method 12: Press Space key (page down)
    print("METHOD 12: Press Space key...")
    web.page.keyboard.press('Space')
    time.sleep(1)
    methods.append(("Press Space", "Pressed"))
    web.take_screenshot("method12_space.png")

    # Print results
    print("\n\n=== RESULTS SUMMARY ===\n")
    for method, result in methods:
        print(f"{method}: {result}")

    print("\n\n✅ Investigation complete!")
    print("Check all screenshots in screenshots/ folder")
    print("Screenshots: investigate_before.png, method1-12.png")

    input("\nPress Enter to close browser...")
    web.close()

if __name__ == "__main__":
    investigate_gmail()
