"""
Test for stock ticker visibility in finance theme home page.
"""
import re
import os


def test_stock_ticker_visibility():
    """Test that the stock ticker has sufficient contrast for visibility."""
    # Path to the finance theme home template
    template_path = os.path.join(
        os.path.dirname(__file__), 
        "../now_lms/templates/themes/finance/overrides/home.j2"
    )
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the ticker div
    ticker_pattern = r'<!-- Stock ticker pattern overlay -->(.*?)</div>'
    ticker_match = re.search(ticker_pattern, content, re.DOTALL)
    
    assert ticker_match, "Stock ticker element not found"
    
    ticker_content = ticker_match.group(1)
    
    # Check for high contrast color (opacity should be >= 0.9 for good visibility)
    color_pattern = r'color:\s*rgba\([^)]+,\s*([0-9.]+)\)'
    color_match = re.search(color_pattern, ticker_content)
    
    assert color_match, "Color property not found in ticker"
    
    opacity = float(color_match.group(1))
    assert opacity >= 0.9, f"Text opacity {opacity} is too low, should be >= 0.9 for good visibility"
    
    # Check that text shadow is present for better readability
    assert 'text-shadow:' in ticker_content, "Text shadow should be present for better readability"
    
    # Check that font-weight is bold
    assert 'font-weight: bold' in ticker_content, "Font should be bold for better visibility"
    
    # Check that the ticker text is present
    assert 'NASDAQ' in ticker_content, "Ticker should contain NASDAQ text"
    assert 'S&P500' in ticker_content, "Ticker should contain S&P500 text"
    assert '📈' in ticker_content, "Ticker should contain chart emoji"
    assert '📊' in ticker_content, "Ticker should contain bar chart emoji"


if __name__ == "__main__":
    test_stock_ticker_visibility()
    print("✅ Stock ticker visibility test passed!")