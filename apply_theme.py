import os

# The path to your CSS file
css_path = os.path.join('app', 'static', 'css', 'styles.css')

# The modern CSS code to append
modern_css = """
/* ========================================= */
/* MODERN UI UPGRADE (Added via Script) */
/* ========================================= */

/* 1. Reset the options container */
.options-div ul {
    padding: 0;
    list-style: none;
    margin-top: 20px;
}

/* 2. Transform List Items into Card Containers */
.options-div li {
    position: relative;
    margin-bottom: 15px;
    height: auto !important; /* Override old height */
    width: 100% !important;  /* Override old width */
    padding: 0 !important;   /* Reset padding */
    border: none !important; /* Remove old border */
    display: block !important; /* Override flex */
    transition: all 0.2s ease;
}

/* 3. Hide the default radio buttons completely */
.options-div input[type="radio"] {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
    z-index: 2;
    margin: 0;
    left: 0;
    top: 0;
}

/* 4. Style the Label as a Modern Card */
.options-div label {
    display: flex;
    align-items: center;
    width: 100%;
    padding: 18px 25px;
    background-color: #ffffff;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 1.1rem;
    color: #2d3748;
    font-weight: 600;
    cursor: pointer;
    margin: 0 !important; /* Reset old margins */
    box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 5. Hover Effect */
.options-div li:hover label {
    border-color: #4299e1;
    background-color: #ebf8ff;
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(66, 153, 225, 0.1);
}

/* 6. Selected State (Active) */
/* When input is checked, style the label immediately following it */
.options-div input[type="radio"]:checked + label {
    background-color: #3182ce;
    color: white;
    border-color: #3182ce;
    box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    transform: scale(1.01);
}

/* 7. Visual "Check" Circle inside the card */
.options-div label::before {
    content: '';
    display: inline-block;
    width: 24px;
    height: 24px;
    margin-right: 15px;
    border: 2px solid #cbd5e0;
    border-radius: 50%;
    background-color: white;
    transition: all 0.2s ease;
    flex-shrink: 0;
}

/* 8. Active Check Circle */
.options-div input[type="radio"]:checked + label::before {
    border-color: white;
    background-color: #4299e1;
    box-shadow: inset 0 0 0 4px white;
}

/* 9. Success Button Modernization */
.btn-success {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
    border: none;
    box-shadow: 0 4px 6px rgba(72, 187, 120, 0.3);
    padding: 12px 40px;
    font-size: 1.1rem;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.btn-success:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(72, 187, 120, 0.4);
}
"""

def apply_theme():
    if not os.path.exists(css_path):
        print(f"❌ Error: Could not find {css_path}")
        return

    print(f"🎨 Found {css_path}")
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if we already applied it to avoid duplication
    if "MODERN UI UPGRADE" in content:
        print("⚠️  Theme already applied! Skipping.")
    else:
        with open(css_path, 'a', encoding='utf-8') as f:
            f.write(modern_css)
        print("✅ Successfully appended modern CSS!")
        print("🚀 Restart your server and refresh the quiz page to see changes.")

if __name__ == "__main__":
    apply_theme()