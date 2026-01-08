import { useTranslation } from 'react-i18next';
import './LanguageSelector.css';

export function LanguageSelector() {
  const { i18n } = useTranslation();

  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
    // 保存到 localStorage
    localStorage.setItem('preferred_language', lang);
  };

  const currentLang = i18n.language;

  return (
    <div className="language-selector">
      <button
        className={currentLang === 'en' ? 'active' : ''}
        onClick={() => changeLanguage('en')}
      >
        English
      </button>
      <button
        className={currentLang === 'zh' ? 'active' : ''}
        onClick={() => changeLanguage('zh')}
      >
        中文
      </button>
      <button
        className={currentLang === 'ja' ? 'active' : ''}
        onClick={() => changeLanguage('ja')}
      >
        日本語
      </button>
    </div>
  );
}

