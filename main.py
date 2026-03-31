import streamlit as st
import os
import pandas as pd
from scrape import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from parse import parse_with_ollama, parse_properties

# Page config
st.set_page_config(
    page_title="Neurawl Scraper",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Main header
st.title("🕷️ Neurawl Scraper")
st.markdown("Scrape websites and extract data with intelligent parsing")

# STEP 1: Scrape Website
st.markdown("---")
st.subheader("Enter URL to Scrape")

col1, col2 = st.columns([4, 1])

with col1:
    url = st.text_input(
        "Website URL",
        placeholder="https://example.com",
        label_visibility="collapsed"
    )

with col2:
    scrape_button = st.button("🔍 Scrape", use_container_width=True, key="scrape_btn")

# Step 1: Scrape the Website
if scrape_button:
    if url:
        with st.spinner("🔄 Scraping the website..."):
            try:
                dom_content = scrape_website(url)
                
                if not dom_content or len(dom_content.strip()) < 100:
                    st.error("❌ No content found. Please check the URL and try again.")
                else:
                    body_content = extract_body_content(dom_content)
                    cleaned_content = clean_body_content(body_content)

                    if not cleaned_content or len(cleaned_content.strip()) < 50:
                        st.error("❌ Content was scraped but appears to be empty.")
                    else:
                        st.session_state.dom_content = cleaned_content
                        char_count = len(cleaned_content)
                        st.success(f"✅ Successfully scraped! ({char_count:,} characters)")

                        with st.expander("📄 View Page Content", expanded=False):
                            st.text_area(
                                "Scraped Content",
                                cleaned_content,
                                height=400,
                                disabled=True,
                                label_visibility="collapsed"
                            )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter a valid website URL")
# STEP 2: Parse Content
st.markdown("---")
st.subheader("Extract Information")

if "dom_content" in st.session_state:
    parse_description = st.text_area(
        "What do you want to extract?",
        placeholder="e.g., 'prices', 'product names', 'contact info', or 'company details'",
        height=80,
        label_visibility="collapsed"
    )

    if st.button("🤖 Parse Content", use_container_width=True, key="parse_btn"):
        if parse_description:
            with st.spinner("🤖 Analyzing content with AI..."):
                try:
                    dom_chunks = split_dom_content(st.session_state.dom_content)
                    print(f"[MAIN] Parsing {len(dom_chunks)} chunks...")
                    
                    # Use intelligent adaptive parser
                    parse_result = parse_properties(dom_chunks, parse_description)
                    
                    # Display results by type
                    st.divider()
                    
                    if parse_result['type'] == 'properties':
                        # Property results with table
                        st.success(f"✅ Found {parse_result['count']} properties")
                        
                        df = pd.DataFrame([{
                            'Price': prop.get('price', '-'),
                            'Beds': prop.get('beds', '-'),
                            'Baths': prop.get('baths', '-'),
                            'Area': prop.get('area', '-'),
                            'Location': prop.get('location', '-')[:40] if prop.get('location') else '-',
                        } for prop in parse_result['data']])
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Export options
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            csv_data = df.to_csv(index=False)
                            st.download_button(
                                label="📥 CSV",
                                data=csv_data,
                                file_name="properties.csv",
                                mime="text/csv"
                            )
                        with col2:
                            import json
                            json_data = json.dumps(parse_result['data'], indent=2)
                            st.download_button(
                                label="📥 JSON",
                                data=json_data,
                                file_name="properties.json",
                                mime="application/json"
                            )
                        with col3:
                            st.download_button(
                                label="📥 TXT",
                                data=parse_result['table'],
                                file_name="properties.txt",
                                mime="text/plain"
                            )
                    
                    elif parse_result['type'] == 'table_text':
                        # Structured table data
                        st.success(f"✅ Extracted {parse_result['count']} items")
                        
                        # Display with better formatting
                        with st.container():
                            st.markdown("**Extracted Data:**")
                            st.code(parse_result['data'], language="text")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 TXT",
                                data=parse_result['data'],
                                file_name="data.txt",
                                mime="text/plain"
                            )
                        with col2:
                            st.download_button(
                                label="📥 CSV",
                                data=parse_result['data'],
                                file_name="data.csv",
                                mime="text/csv"
                            )
                    
                    elif parse_result['type'] == 'list':
                        # List results
                        st.success(f"✅ Found {parse_result['count']} results")
                        
                        with st.container():
                            st.markdown("**Results:**")
                            result_lines = parse_result['data'].strip().split('\n')
                            for idx, line in enumerate(result_lines, 1):
                                if line.strip():
                                    st.write(f"**{idx}.** {line.strip()}")
                        
                        st.download_button(
                            label="📥 Download Results",
                            data=parse_result['data'],
                            file_name="results.txt",
                            mime="text/plain"
                        )
                    
                    else:  # text type
                        # Narrative text results
                        st.success("✅ Analysis Complete")
                        
                        with st.container():
                            st.markdown("**Result:**")
                            st.info(parse_result['data'])
                        
                        st.download_button(
                            label="📥 Download Analysis",
                            data=parse_result['data'],
                            file_name="analysis.txt",
                            mime="text/plain"
                        )
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    with st.expander("📋 Details"):
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.warning("⚠️ Please describe what you want to extract")
else:
    st.info("💡 Tip: Scrape a website first to enable content parsing")
