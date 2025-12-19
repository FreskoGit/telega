require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

// Инициализация приложения
const app = express();

// Настройка Supabase
const supabase = createClient(
    process.env.SUPABASE_URL || 'https://gcxujsoqiywkiruzrqdg.supabase.co',
    process.env.SUPABASE_KEY || 'ваш_секретный_ключ_тут'
);

// Безопасность
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
            mediaSrc: ["'self'"],
            connectSrc: ["'self'"]
        }
    },
    hidePoweredBy: true,
    noSniff: true,
    xssFilter: true,
    frameguard: { action: 'deny' }
}));

// Ограничение запросов
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 минут
    max: 100 // лимит запросов
});
app.use('/api/', limiter);

// CORS настройка
const corsOptions = {
    origin: function(origin, callback) {
        // Разрешаем только с вашего домена
        const allowedOrigins = [
            'http://localhost:3000',
            'https://ваш-домен.com',
            'https://www.ваш-домен.com'
        ];
        
        if (!origin || allowedOrigins.indexOf(origin) !== -1) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    optionsSuccessStatus: 200
};
app.use(cors(corsOptions));

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// API endpoint для счетчика
app.post('/api/counter', async (req, res) => {
    try {
        // Валидация IP (опционально)
        const clientIP = req.ip || req.connection.remoteAddress;
        
        // Проверка на ботов (простая)
        const userAgent = req.get('User-Agent') || '';
        const isBot = /bot|crawl|spider|scrape|curl|wget/i.test(userAgent);
        
        if (isBot) {
            return res.status(403).json({ error: 'Access denied' });
        }

        // Получаем текущее значение
        const { data: currentData, error: fetchError } = await supabase
            .from('counter')
            .select('value')
            .eq('id', 1)
            .single();

        let newValue;
        
        if (fetchError || !currentData) {
            // Создаем новую запись
            newValue = 1;
            const { error: insertError } = await supabase
                .from('counter')
                .insert({ id: 1, value: newValue });
                
            if (insertError) {
                throw insertError;
            }
        } else {
            // Увеличиваем счетчик
            newValue = currentData.value + 1;
            const { error: updateError } = await supabase
                .from('counter')
                .update({ value: newValue })
                .eq('id', 1);
                
            if (updateError) {
                throw updateError;
            }
        }

        // Логирование (опционально)
        console.log(`[${new Date().toISOString()}] Counter update: ${newValue} from IP: ${clientIP}`);

        // Возвращаем результат
        res.json({ 
            success: true, 
            count: newValue,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('API Error:', error);
        res.status(500).json({ 
            success: false, 
            error: 'Internal server error',
            fallback: true
        });
    }
});

// Защищенный endpoint для получения статистики (только для админа)
app.get('/api/admin/stats', async (req, res) => {
    // Простая проверка (лучше использовать JWT)
    const adminToken = req.headers['x-admin-token'];
    
    if (adminToken !== process.env.ADMIN_TOKEN) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    try {
        const { data } = await supabase
            .from('counter')
            .select('*')
            .eq('id', 1)
            .single();
            
        res.json({ stats: data });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        service: 'Fresko Counter API'
    });
});

// Все остальные маршруты ведут на index.html
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Обработка ошибок
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

// Запуск сервера
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✅ Server running on port ${PORT}`);
    console.log(`🔒 Security headers enabled`);
    console.log(`🌐 Serving from: ${path.join(__dirname, '../public')}`);
});