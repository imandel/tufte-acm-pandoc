// Citation back-navigation with contextual button
document.addEventListener('DOMContentLoaded', function() {
    let lastScrollPosition = 0;
    let backButton = null;
    let currentCitationTarget = null;
    
    // Create the floating back button
    function createBackButton() {
        if (backButton) return backButton;
        
        backButton = document.createElement('button');
        backButton.innerHTML = '↩';
        backButton.className = 'citation-back-button';
        backButton.style.cssText = `
            position: absolute;
            background-color: #3498db;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-family: et-book, Georgia, serif;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s, visibility 0.3s;
            top: -8px;
            right: -80px;
            white-space: nowrap;
        `;
        
        // Handle back button click
        backButton.addEventListener('click', function() {
            if (lastScrollPosition > 0) {
                window.scrollTo({
                    top: lastScrollPosition,
                    behavior: 'smooth'
                });
            } else {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
            hideBackButton();
        });
        
        return backButton;
    }
    
    // Show the back button next to a citation
    function showBackButton(citationElement) {
        const button = createBackButton();
        
        // Remove from previous location
        if (button.parentNode) {
            button.parentNode.removeChild(button);
        }
        
        // Make sure the citation element has relative positioning
        citationElement.style.position = 'relative';
        
        // Add to the citation element
        citationElement.appendChild(button);
        
        // Show the button
        setTimeout(() => {
            button.style.opacity = '1';
            button.style.visibility = 'visible';
        }, 100);
    }
    
    // Hide the back button
    function hideBackButton() {
        if (backButton) {
            backButton.style.opacity = '0';
            backButton.style.visibility = 'hidden';
        }
    }
    
    // Store scroll position and show back button when clicking citations
    const citationLinks = document.querySelectorAll('a[href^="#ref-"]');
    citationLinks.forEach(link => {
        link.addEventListener('click', function() {
            lastScrollPosition = window.scrollY;
            
            // Get the target citation element
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                currentCitationTarget = targetElement;
                
                // Show back button after navigation completes
                setTimeout(() => {
                    showBackButton(targetElement);
                }, 300);
            }
        });
    });
    
    // Hide back button when scrolling away from the bibliography
    let hideTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(hideTimeout);
        
        if (currentCitationTarget && backButton) {
            const rect = currentCitationTarget.getBoundingClientRect();
            
            // If the citation is no longer visible, hide the button
            if (rect.bottom < 0 || rect.top > window.innerHeight) {
                hideTimeout = setTimeout(() => {
                    hideBackButton();
                }, 1000);
            }
        }
    });
    
    // Dark mode support
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTimeout(() => {
            if (backButton) {
                backButton.style.backgroundColor = '#65b0ee';
            }
        }, 100);
    }
});