/**
 * Gerenciador de Perfis Natais Salvos Localmente (LocalStorage + Cookies).
 * Permite cadastrar, salvar e alternar perfis pessoais diretamente no navegador,
 * com total privacidade e sem dependência de banco de dados no servidor.
 */

(function (window) {
    'use strict';

    const STORAGE_KEY = 'astro_natal_saved';
    const COOKIE_NAME = 'astro_saved_charts';
    const MAX_PROFILES = 30;

    // Helper: leitura de cookies
    function getCookie(name) {
        const matches = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + '=([^;]*)'));
        return matches ? decodeURIComponent(matches[1]) : null;
    }

    // Helper: escrita em cookies (1 ano de expiração)
    function setCookie(name, value, days) {
        days = days || 365;
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = name + '=' + encodeURIComponent(value) + ';expires=' + d.toUTCString() + ';path=/;SameSite=Lax';
    }

    const NatalStorage = {
        /**
         * Retorna a lista de pessoas salvas, sincronizando localStorage e cookies.
         */
        getAll: function () {
            let list = [];
            try {
                const rawLs = localStorage.getItem(STORAGE_KEY);
                if (rawLs) {
                    list = JSON.parse(rawLs);
                }
            } catch (e) {
                console.warn('Falha ao ler localStorage:', e);
            }

            // Fallback para cookies se o localStorage estiver vazio
            if (!list || list.length === 0) {
                try {
                    const rawCookie = getCookie(COOKIE_NAME);
                    if (rawCookie) {
                        list = JSON.parse(rawCookie);
                        if (Array.isArray(list) && list.length > 0) {
                            try {
                                localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
                            } catch (e) {}
                        }
                    }
                } catch (e) {
                    console.warn('Falha ao ler cookie:', e);
                }
            }

            return Array.isArray(list) ? list : [];
        },

        /**
         * Salva ou atualiza uma pessoa no registro local.
         */
        save: function (person) {
            if (!person || !person.date || person.lat === undefined || person.lon === undefined) {
                return false;
            }

            const list = this.getAll();
            const label = (person.label && person.label.trim()) ? person.label.trim() : ('Mapa ' + person.date);
            const id = person.id || ('natal_' + Date.now() + '_' + Math.floor(Math.random() * 1000));

            const profile = {
                id: id,
                label: label,
                date: person.date,
                time: person.time || '12:00',
                time_known: person.time_known !== false && person.time_known !== '0' && person.time_known !== 0,
                place: person.place || '',
                lat: parseFloat(person.lat),
                lon: parseFloat(person.lon),
                tz: person.tz || '',
                house_system: person.house_system || 'P',
                updated_at: new Date().toISOString()
            };

            // Remover duplicata idêntica se houver (mesmo label e data/local)
            const filtered = list.filter(p => !(p.label.toLowerCase() === profile.label.toLowerCase() && p.date === profile.date));
            filtered.unshift(profile);

            const trimmed = filtered.slice(0, MAX_PROFILES);
            const serialized = JSON.stringify(trimmed);

            try {
                localStorage.setItem(STORAGE_KEY, serialized);
            } catch (e) {}

            try {
                setCookie(COOKIE_NAME, serialized, 365);
            } catch (e) {}

            return true;
        },

        /**
         * Remove uma pessoa da lista salva.
         */
        remove: function (idOrLabel) {
            let list = this.getAll();
            list = list.filter(p => p.id !== idOrLabel && p.label !== idOrLabel);
            const serialized = JSON.stringify(list);

            try {
                localStorage.setItem(STORAGE_KEY, serialized);
            } catch (e) {}

            try {
                setCookie(COOKIE_NAME, serialized, 365);
            } catch (e) {}

            return list;
        },

        /**
         * Verifica se uma pessoa específica já está salva.
         */
        isSaved: function (date, label) {
            const list = this.getAll();
            return list.some(p => p.date === date && (!label || p.label.toLowerCase() === label.toLowerCase()));
        },

        /**
         * Monta a URL para uma aba do módulo natal.
         */
        getUrl: function (person, tab) {
            tab = tab || 'chart';
            const params = new URLSearchParams();
            if (person.label) params.set('label', person.label);
            params.set('date', person.date);
            params.set('time', person.time || '12:00');
            if (person.time_known === false || person.time_known === '0') {
                params.set('time_known', '0');
            }
            params.set('lat', person.lat);
            params.set('lon', person.lon);
            if (person.tz) params.set('tz', person.tz);
            if (person.place) params.set('place', person.place);
            if (person.house_system) params.set('house_system', person.house_system);

            return '/natal/' + tab + '?' + params.toString();
        },

        /**
         * Limpa todos os perfis salvos.
         */
        clearAll: function () {
            try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
            try { setCookie(COOKIE_NAME, '', -1); } catch (e) {}
        }
    };

    window.NatalStorage = NatalStorage;

})(window);
