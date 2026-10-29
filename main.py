import base64
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import AzureOpenAI, APIError
import streamlit as st
import pandas as pd
from pypdf import PdfReader

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="InteriorAI Studio - Agente de Design de Interiores",
    page_icon="🏠",
    layout="wide"
)

# --- FUNÇÃO AUXILIAR PARA ENCODER IMAGENS ---
def encode_image(image_file):
    """Converte o arquivo de imagem em uma string Base64."""
    return base64.b64encode(image_file.read()).decode('utf-8')

# --- CONFIGURAÇÃO DA SIDEBAR ---
st.sidebar.header("⚙️ Configurações & Ferramentas")

# Credenciais Azure OpenAI
azure_endpoint = st.sidebar.text_input("Azure OpenAI Endpoint", value=os.getenv("AZURE_OPENAI_ENDPOINT", ""), type="default")
azure_key = st.sidebar.text_input("Azure OpenAI API Key", value=os.getenv("AZURE_OPENAI_API_KEY", ""), type="password")
deployment_name = st.sidebar.text_input("Deployment Name (ex: gpt-4o)", value=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"))
api_version = st.sidebar.text_input("API Version", value=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))

st.sidebar.divider()

# Nova Ferramenta: Upload de Foto do Ambiente (Uso do base64)
st.sidebar.subheader("📸 Foto do Ambiente")
uploaded_image = st.sidebar.file_uploader("Envie a foto do seu espaço", type=["jpg", "jpeg", "png"])
image_base64 = None

if uploaded_image is not None:
    st.sidebar.image(uploaded_image, caption="Foto do Ambiente", use_container_width=True)
    image_base64 = encode_image(uploaded_image)
    st.sidebar.success("Foto carregada com sucesso!")

st.sidebar.divider()

# Ferramenta 1: Leitor de PDF (pypdf)
st.sidebar.subheader("📄 Leitor de Briefing/Catálogo (PDF)")
uploaded_pdf = st.sidebar.file_uploader("Envie um PDF de referência", type=["pdf"])
pdf_context = ""
if uploaded_pdf is not None:
    try:
        reader = PdfReader(uploaded_pdf)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pdf_context += f"\n--- Página {i+1} do PDF ---\n" + text
        st.sidebar.success(f"PDF lido ({len(reader.pages)} págs)!")
    except Exception as e:
        st.sidebar.error(f"Erro ao ler PDF: {e}")

# Ferramenta 2: Planilha de Orçamento (pandas)
st.sidebar.subheader("📊 Planilha de Orçamento (CSV/Excel)")
uploaded_excel = st.sidebar.file_uploader("Envie sua tabela de custos", type=["csv", "xlsx"])
df_context = ""
if uploaded_excel is not None:
    try:
        if uploaded_excel.name.endswith('.csv'):
            df = pd.read_csv(uploaded_excel)
        else:
            df = pd.read_excel(uploaded_excel)
        df_context = f"\n--- Dados do Orçamento ---\n" + df.to_string(index=False)
        st.sidebar.success("Planilha carregada!")
    except Exception as e:
        st.sidebar.error(f"Erro ao ler planilha: {e}")

# Ferramenta 3: Scraping Web (requests + bs4)
st.sidebar.subheader("🌐 Inspirador Web (Scraper)")
url_inspiration = st.sidebar.text_input("URL de inspiração de design")
scraped_text = ""
if st.sidebar.button("Extrair Conteúdo do Site") and url_inspiration:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url_inspiration, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            scraped_text = f"\n--- Conteúdo extraído de {url_inspiration} ---\n" + soup.get_text(separator=' ', strip=True)[:3000]
            st.sidebar.success("Conteúdo extraído!")
        else:
            st.sidebar.error(f"Erro HTTP: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"Erro ao acessar URL: {e}")

# --- SYSTEM PROMPT COSTAR COM RAO ---
SYSTEM_PROMPT = """
# SYSTEM PROMPT: AGENTE ESPECIALISTA EM DESIGN DE INTERIORES

[CONTEXT]
Você é o "InteriorAI Studio", um agente virtual especialista em Design de Interiores, Arquitetura e Decoração. Você possui profundo conhecimento em ergonomia, psicologia das cores, iluminação (luminotécnica), escolha de materiais/texturas e aproveitamento inteligente de espaços residenciais e comerciais. Quando fotos do ambiente forem fornecidas, você DEVE analisá-las detalhadamente (disposição do espaço, iluminação natural, piso, paredes, teto e móveis existentes).

[OBJECTIVE]
Seu objetivo é guiar o usuário desde a fase inicial de ideias (briefing) até a criação de um conceito de design completo, personalizado, funcional e esteticamente harmonioso, respeitando as restrições físicas e orçamentárias informadas.

[STYLE]
Atencioso, criativo, profissional, elegante e focado em soluções práticas. Sua comunicação deve ser acessível e inspiradora, evitando jargões técnicos excessivos sem explicação.

[TONE]
Acolhedor, empático, consultivo e refinado.

[AUDIENCE]
Pessoas buscando reformar, redecorar ou planejar um ambiente, desde leigos que precisam de orientação total até profissionais buscando insights de composição.

[RESPONSE FORMAT - RAO (REASONING, ACTION, OUTPUT)]
Para cada interação complexa ou solicitação de projeto, você DEVE estruturar sua resposta internamente e entregar o resultado seguindo a metodologia RAO (Raciocínio, Ação, Saída):

1. REASONING (Raciocínio / Análise Interna)
   - Analise os dados e fotos fornecidas pelo usuário (dimensões visuais, pontos fortes/fracos do ambiente atual).
   - Avalie os desafios ergonômicos, iluminação natural/artificial e circulação.
   - Identifique lacunas de informação no briefing se houver.

2. ACTION (Ação Estratégica)
   - Defina o conceito de design (estilo recomendado, paleta de cores, materiais/texturas).
   - Planeje a distribuição espacial (layout, setorização e o que manter/trocar).
   - Monte a seleção de itens de iluminação, móveis e objetos decorativos.

3. OUTPUT (Saída para o Usuário)
   - Apresente a proposta final ao usuário de forma clara, funcional e visualmente organizada (utilizando listas, tópicos e negritos).
"""

# --- INTERFACE PRINCIPAL ---
st.title("🏠 InteriorAI Studio")
st.markdown("Seu assistente de arquitetura e design com análise visual e metodologia **RAO**.")

# Histórico da conversa
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Olá! Sou o InteriorAI Studio. Anexe a foto do seu espaço na barra lateral ou envie uma mensagem para começarmos o seu projeto de interiores!"}
    ]

# Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Processar entrada do usuário
if prompt := st.chat_input("Digite sua dúvida ou pedido sobre o ambiente..."):
    if not azure_endpoint or not azure_key:
        st.error("Por favor, configure o Endpoint e a Chave do Azure OpenAI na barra lateral.")
    else:
        # Montar o texto completo com contextos adicionais (PDF, Planilha e Web)
        extra_info = ""
        if pdf_context:
            extra_info += f"\n\n[Contexto do PDF anexado]: {pdf_context}"
        if df_context:
            extra_info += f"\n\n[Contexto da Planilha anexada]: {df_context}"
        if scraped_text:
            extra_info += f"\n\n[Contexto da URL anexada]: {scraped_text}"

        user_text = prompt + extra_info

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                api_version=api_version
            )

            # Estruturar as mensagens do Chat
            messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Histórico anterior (apenas texto)
            for m in st.session_state.messages[:-1]:
                messages_payload.append({"role": m["role"], "content": m["content"]})

            # Montagem do conteúdo do último envio (Permite Multimodalidade se houver imagem)
            if image_base64:
                user_content = [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            else:
                user_content = user_text

            messages_payload.append({"role": "user", "content": user_content})

            with st.chat_message("assistant"):
                with st.spinner("Analisando foto do ambiente, ergonomia e gerando proposta (RAO)..."):
                    response = client.chat.completions.create(
                        model=deployment_name,
                        messages=messages_payload,
                        temperature=0.7,
                        max_tokens=2500
                    )
                    assistant_reply = response.choices[0].message.content
                    st.markdown(assistant_reply)

            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        except APIError as e:
            st.error(f"Erro na API do Azure OpenAI: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")