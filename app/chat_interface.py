import streamlit as st
from api_utils import get_api_response

def display_chat_interface():
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask Mr. K"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generating response..."):
            response = get_api_response(prompt, st.session_state.session_id, st.session_state.model)
            
            if response:
                st.session_state.session_id = response.get('session_id')
                
                # Add attribution if the response used the default document
                response_content = response['answer']
                if 'OpenStaxHSPhysics.pdf' in str(response.get('sources', [])):
                    response_content += "\n\n---\n*Response includes content from OpenStax High School Physics (CC BY 4.0)*"
                
                st.session_state.messages.append({"role": "assistant", "content": response_content})
                
                with st.chat_message("assistant"):
                    st.markdown(response_content)
            else:
                st.error("Failed to get a response from the API. Please try again.")

    # Add attribution footer at the bottom
    st.markdown("<br>" * 2, unsafe_allow_html=True)  # Add some space
    with st.container():
        st.markdown("""
        <div style='border-top: 1px solid #e6e6e6; padding-top: 1em; margin-top: 2em; font-size: 0.8em; color: #666; text-align: center;'>
        Responses may include content from OpenStax High School Physics,<br>
        licensed under <a href='https://creativecommons.org/licenses/by/4.0/deed.en'>CC BY 4.0</a> by Texas Education Agency (TEA)
        </div>
        """, unsafe_allow_html=True)