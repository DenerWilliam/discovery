"""Tabela de assinaturas de tecnologias. Enxuta e fácil de estender.

Cada entrada: ``nome``, ``categoria`` e um ou mais critérios (todos em minúsculas):
``html`` (trechos no HTML), ``urls`` (trechos nas URLs requisitadas), ``cookies``
(prefixos de nome de cookie) e ``headers`` (``{cabeçalho: trecho}``).
"""

from __future__ import annotations

ECOMMERCE = "e-commerce/CMS"
MARKETING = "marketing e analytics"
CHAT = "chat e WhatsApp"
PAGAMENTO = "pagamentos"
CDN = "CDN e infraestrutura"

SIGNATURES: list[dict] = [
    # Plataformas de e-commerce e CMS
    {"nome": "VTEX", "categoria": ECOMMERCE, "urls": ["vtexassets.com", "vteximg.com.br", "vtexcommercestable"], "cookies": ["vtex"], "html": ["vtex.render"]},
    {"nome": "Shopify", "categoria": ECOMMERCE, "urls": ["cdn.shopify.com", "myshopify.com"], "cookies": ["_shopify"], "html": ["shopify.theme"]},
    {"nome": "Tray", "categoria": ECOMMERCE, "urls": ["tcdn.com.br", "traycdn", "tray.com.br"], "cookies": ["tray"], "html": []},
    {"nome": "Nuvemshop", "categoria": ECOMMERCE, "urls": ["nuvemshop", "tiendanube", "mitiendanube"], "html": ["nuvemshop"]},
    {"nome": "Loja Integrada", "categoria": ECOMMERCE, "urls": ["lojaintegrada.com.br", "awsli.com.br"], "html": []},
    {"nome": "Wake (Fbits)", "categoria": ECOMMERCE, "urls": ["fbitsstatic.net", "wake.tech", "fbits.net"], "html": []},
    {"nome": "Magento", "categoria": ECOMMERCE, "urls": ["/static/frontend/", "mage/"], "cookies": ["mage-"], "html": ["magento", "mage/cookies"]},
    {"nome": "WooCommerce", "categoria": ECOMMERCE, "urls": ["woocommerce"], "cookies": ["woocommerce_"], "html": ["woocommerce"]},
    {"nome": "WordPress", "categoria": ECOMMERCE, "urls": ["/wp-content/", "/wp-includes/"], "html": ["wp-content", 'name="generator" content="wordpress']},
    {"nome": "Wix", "categoria": ECOMMERCE, "urls": ["wixstatic.com", "parastorage.com"], "headers": {"x-wix-request-id": ""}},
    {"nome": "Jet e-commerce (Plataforma Neo)", "categoria": ECOMMERCE, "urls": ["jetassets.com.br", "plataformaneo.com.br"], "headers": {"powered": "jet-neo", "content-security-policy": "plataformaneo"}},
    {"nome": "Yampi", "categoria": ECOMMERCE, "urls": ["yampi.io", "yampi.com.br"]},
    {"nome": "Odoo", "categoria": ECOMMERCE, "urls": ["/web/assets/", "/web/static/"], "html": ["odoo", "data-oe-"]},
    # Marketing e analytics
    {"nome": "Google Analytics", "categoria": MARKETING, "urls": ["google-analytics.com", "googletagmanager.com/gtag"], "cookies": ["_ga"]},
    {"nome": "Google Tag Manager", "categoria": MARKETING, "urls": ["googletagmanager.com/gtm.js"], "html": ["gtm-"]},
    {"nome": "Meta Pixel", "categoria": MARKETING, "urls": ["connect.facebook.net", "facebook.com/tr"], "cookies": ["_fbp"]},
    {"nome": "RD Station", "categoria": MARKETING, "urls": ["rdstation", "d335luupugsy2.cloudfront.net"]},
    {"nome": "HubSpot", "categoria": MARKETING, "urls": ["hs-scripts.com", "hsforms", "hubspot.com"], "cookies": ["hubspotutk"]},
    {"nome": "Google Ads / DoubleClick", "categoria": MARKETING, "urls": ["googleads.g.doubleclick.net", "doubleclick.net"]},
    {"nome": "Hotjar", "categoria": MARKETING, "urls": ["hotjar.com"], "cookies": ["_hjsession"]},
    {"nome": "Microsoft Clarity", "categoria": MARKETING, "urls": ["clarity.ms"]},
    {"nome": "TikTok Pixel", "categoria": MARKETING, "urls": ["analytics.tiktok.com"]},
    {"nome": "Mailchimp", "categoria": MARKETING, "urls": ["chimpstatic.com", "list-manage.com"]},
    # Chat e WhatsApp
    {"nome": "WhatsApp (link/botão)", "categoria": CHAT, "html": ["api.whatsapp.com", "wa.me/"]},
    {"nome": "Tawk.to", "categoria": CHAT, "urls": ["tawk.to"]},
    {"nome": "JivoChat", "categoria": CHAT, "urls": ["jivosite.com"]},
    {"nome": "Zendesk", "categoria": CHAT, "urls": ["zopim.com", "zendesk.com", "zdassets.com"]},
    {"nome": "Intercom", "categoria": CHAT, "urls": ["intercom.io", "intercomcdn.com"]},
    {"nome": "Movidesk", "categoria": CHAT, "urls": ["movidesk.com"]},
    # Pagamentos
    {"nome": "Mercado Pago", "categoria": PAGAMENTO, "urls": ["mercadopago.com", "mercadolibre.com"], "html": ["mercadopago"]},
    {"nome": "PagSeguro", "categoria": PAGAMENTO, "urls": ["pagseguro.uol.com.br", "pagbank"]},
    {"nome": "Pagar.me", "categoria": PAGAMENTO, "urls": ["pagar.me"]},
    {"nome": "Stripe", "categoria": PAGAMENTO, "urls": ["js.stripe.com"]},
    {"nome": "PayPal", "categoria": PAGAMENTO, "urls": ["paypal.com", "paypalobjects.com"]},
    # CDN e infraestrutura
    {"nome": "Cloudflare", "categoria": CDN, "headers": {"server": "cloudflare"}, "cookies": ["__cf_bm", "cf_clearance"]},
    {"nome": "Amazon CloudFront", "categoria": CDN, "headers": {"via": "cloudfront", "x-amz-cf-id": ""}},
    {"nome": "Akamai", "categoria": CDN, "headers": {"server": "akamai"}},
    {"nome": "Google reCAPTCHA", "categoria": CDN, "urls": ["google.com/recaptcha", "gstatic.com/recaptcha"]},
]
