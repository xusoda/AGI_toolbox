import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// 翻译资源
import enTranslations from './locales/en/translation.json';
import zhTranslations from './locales/zh/translation.json';
import jaTranslations from './locales/ja/translation.json';

i18n
  .use(LanguageDetector)  // 自动检测用户语言
  .use(initReactI18next)  // 连接 react-i18next
  .init({
    resources: {
      en: { translation: enTranslations },
      zh: { translation: zhTranslations },
      ja: { translation: jaTranslations },
    },
    fallbackLng: 'en',  // 默认语言
    debug: false,
    interpolation: {
      escapeValue: false,  // React 已经转义
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;

