require('dotenv').config();
const express = require('express');
const Stripe = require('stripe');
const TelegramBot = require('node-telegram-bot-api');

// Configurações
const app = express();
const stripe = Stripe(process.env.STRIPE_SECRET_KEY);
const bot = new TelegramBot(process.env.TLEGRAM_BOT_TOKEN, { polling: false });

// A URL do seu grupo VIP
const VIP_GROUP_ID = process.env.TELEGRAM_GROUP_ID;

// Middleware para receber o JSON do Stripe (Raw Body é necessário para segurança)
app.post('/webhook', express.raw({ type: 'application/json' }), async (request, response) => {
    const sig = request.headers['stripe-signature'];
    const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

    let event;

    try {
        // Verifica se a mensagem veio mesmo do Stripe
        event = stripe.webhooks.constructEvent(request.body, sig, endpointSecret);
    } catch (err) {
        console.log(` Erro de verificação: ${err.message}`);
        return response.status(400).send(`Webhook Error: ${err.message}`);
    }

    // Lógica principal
    if (event.type === 'invoice.payment_succeeded') {
        const invoice = event.data.object;
        const customerEmail = invoice.customer_email || 'email não encontrado';
        
        // Verifica se é a primeira cobrança (fim do trial)
        // Você pode ajustar essa lógica conforme necessário
        console.log(`💰 Pagamento confirmado para: ${customerEmail}`);

        // Chama a função de entrega
        await entregarAcessoVIP(customerEmail);
    }

    if (event.type === 'customer.subscription.deleted') {
        // Lógica para quando o cara cancela (remover do grupo)
        console.log("🚫 Assinatura cancelada.");
    }

    response.send();
});

// Função que libera o acesso
async function entregarAcessoVIP(emailCliente) {
    try {
        // 1. Cria um link de convite único que expira em 1 hora
        const linkResponse = await bot.createChatInviteLink(VIP_GROUP_ID, {
            expire_date: Math.floor(Date.now() / 1000) + 3600, // 1 hora
            creates_join_request: false 
        });

        const inviteLink = linkResponse.invite_link;

        // 2. Aqui você pode enviar esse link por email (usando Nodemailer)
        // ou salvar num banco de dados.
        
        console.log(`✅ Link gerado para ${emailCliente}: ${inviteLink}`);
        
        // Opcional: Manda mensagem num grupo de ADMINS para você saber quem entrou
        // bot.sendMessage('SEU_ID_PESSOAL', `🎉 Novo VIP! Email: ${emailCliente}\nLink: ${inviteLink}`);

    } catch (error) {
        console.error('Erro ao gerar link:', error);
    }
}

// Inicia o servidor
const PORT = process.env.PORT || 4242;
app.listen(PORT, () => console.log(`🚀 Servidor rodando na porta ${PORT}`));