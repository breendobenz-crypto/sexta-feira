# gerar_pdf_vip.py - Gera o PDF do Guia VIP Sexta-Feira Advanced
from fpdf import FPDF

class PDFGuide(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(138, 43, 226)  # Roxo da marca
        self.cell(0, 10, 'SEXTA-FEIRA ADVANCED | GUIA DO USUARIO VIP', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(138, 43, 226)
        self.cell(0, 10, title, 0, 1, 'L')
        self.set_draw_color(138, 43, 226)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 6, body)
        self.ln()

    def warning_box(self, text):
        self.set_fill_color(255, 245, 245)
        self.set_draw_color(220, 50, 50)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(200, 0, 0)
        self.multi_cell(0, 6, f' AVISO: {text}', 1, 'L', True)
        self.ln()

    def tip_box(self, text):
        self.set_fill_color(240, 255, 245)
        self.set_draw_color(0, 180, 100)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(0, 120, 60)
        self.multi_cell(0, 6, f' DICA: {text}', 1, 'L', True)
        self.ln()

def generate_pdf():
    pdf = PDFGuide()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ================= CAPA =================
    pdf.ln(50)
    pdf.set_font('Helvetica', 'B', 36)
    pdf.set_text_color(138, 43, 226)
    pdf.cell(0, 15, 'SEXTA-FEIRA', 0, 1, 'C')
    pdf.set_font('Helvetica', 'B', 28)
    pdf.cell(0, 15, 'ADVANCED', 0, 1, 'C')
    pdf.ln(15)
    pdf.set_font('Helvetica', 'I', 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, 'Guia de Inicializacao VIP', 0, 1, 'C')
    pdf.ln(25)
    pdf.set_font('Helvetica', '', 13)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, '"Deixe a Inteligencia Artificial trabalhar por voce enquanto voce dorme."', 0, 'C')
    pdf.ln(40)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, 'Versao 1.0 | Trading Autonomo com IA', 0, 1, 'C')

    # ================= PÁGINA 2: BEM-VINDO =================
    pdf.add_page()
    pdf.chapter_title('1. Bem-vindo ao Futuro do Trading')
    welcome_text = (
        "Parabens por adquirir o acesso ao Sexta-Feira Advanced. Voce agora faz parte de uma plataforma SaaS exclusiva que utiliza Inteligencia Artificial para operar no mercado de criptomoedas via OKX 24 horas por dia.\n\n"
        "PASSO 1: Acesse o Dashboard\n"
        "1. Abra o link do seu dashboard exclusivo: https://sexta-feira-wm1s.onrender.com\n"
        "2. Utilize o E-mail e Senha fornecidos no e-mail de confirmacao de compra (Whop).\n"
        "3. Insira seus dados na tela de login e clique em 'ACESSAR'."
    )
    pdf.chapter_body(welcome_text)
    pdf.tip_box("Mantenha seu e-mail e senha salvos em um gerenciador de senhas seguro.")

    # ================= PÁGINA 3: SEGURANÇA OKX =================
    pdf.chapter_title('2. Conectando a Exchange (OKX)')
    security_text = (
        "Para o robo operar, ele precisa de acesso a sua conta na OKX. SEUS FUNDOS NUNCA SAEM DA CORRETORA. Nos usamos apenas chaves de API criptografadas.\n\n"
        "Siga este passo a passo na OKX:\n"
        "1. Faca login na sua conta da OKX e va em 'Minha Conta' > 'API'.\n"
        "2. Clique em 'Criar Nova API' e de um nome (ex: Sexta-Feira Bot).\n\n"
        "PERMISSOES DA API (MUITO IMPORTANTE):\n"
        " - Marcar: Read (Leitura) e Trade (Negociacao)\n"
        " - NAO MARCAR: Transfer ou Withdraw (Saque). O robo nao precisa e nao deve ter permissao para sacar seus fundos.\n\n"
        "3. Crie uma 'Passphrase' (senha para esta chave) e copie os 3 codigos gerados:\n"
        "   - API Key | Secret Key | Passphrase"
    )
    pdf.chapter_body(security_text)
    pdf.warning_box("Nunca compartilhe sua Passphrase ou Secret Key com terceiros. Nosso sistema as criptografa automaticamente ao salvar.")

    # ================= PÁGINA 4: ATIVAÇÃO =================
    pdf.chapter_title('3. Ativando o Robo no Dashboard')
    activation_text = (
        "1. Volte ao Dashboard Sexta-Feira e clique na aba 'Configuracoes' (engrenagem).\n"
        "2. Role ate a secao 'Chaves API da OKX'.\n"
        "3. Cole a API Key, Secret e Passphrase nos campos correspondentes.\n"
        "4. Clique em 'Testar Conexao'. Se der certo, clique em 'Salvar Chaves'.\n\n"
        "SUCESSO! O robo esta ativo.\n"
        "Em ate 2 minutos, o sistema detectara sua conexao e comecara a escanear o mercado (BTC, ETH, SOL) em busca de oportunidades de alta probabilidade."
    )
    pdf.chapter_body(activation_text)

    # ================= PÁGINA 5: NAVEGAÇÃO E DICAS =================
    pdf.chapter_title('4. Navegacao e Dicas de Ouro')
    nav_text = (
        "ENTENDA O PAINEL:\n"
        " - Mercado: Cotacoes em tempo real e graficos interativos do TradingView.\n"
        " - Posicoes: Acompanhe seus trades abertos, preco de entrada e PnL atual.\n"
        " - Historico: Registro completo de todas as operacoes fechadas com raciocinio da IA.\n"
        " - Terminal IA: Veja o 'pensamento' da inteligencia artificial em tempo real.\n\n"
        "DICAS PARA VIPs:\n"
        "1. Paciencia: O bot opera baseado em score de confianca. Se o mercado estiver lateral, ele pode nao operar. Isso e seguranca.\n"
        "2. Gestao de Risco: O robo usa Stop Loss automatico, mas monitore sua conta regularmente pelo Telegram VIP ou Dashboard.\n"
        "3. Saldo: Mantenha saldo em USDT (dolar) na sua conta OKX para que o robo consiga abrir posicoes."
    )
    pdf.chapter_body(nav_text)

    # ================= PÁGINA 6: SUPORTE E DISCLAIMER =================
    pdf.chapter_title('5. Suporte e Aviso Legal')
    support_text = (
        "CANAL DE AJUDA:\n"
        " - Telegram VIP: Envie '/suporte' no grupo exclusivo.\n"
        " - E-mail: suporte@sextafeira.com\n"
        " - Central de Ajuda: https://whop.com/sexta-feira-advanced\n\n"
        "AVISO DE RISCO:\n"
        "O trading de criptomoedas envolve alto risco de perda de capital. O Sexta-Feira Advanced e uma ferramenta de automacao e analise. Resultados passados nao garantem lucros futuros. Opere com responsabilidade e apenas com capital que voce pode perder."
    )
    pdf.chapter_body(support_text)
    
    pdf.warning_box("Este guia e confidencial. Distribua-o apenas para usuarios autorizados.")

    # Salvar
    output_filename = "Guia_VIP_Sexta_Feira_Advanced.pdf"
    pdf.output(output_filename)
    print(f"✅ PDF gerado com sucesso: {output_filename}")
    print("📂 Abra o arquivo na mesma pasta deste script.")

if __name__ == "__main__":
    generate_pdf()