import { useTranslation } from 'react-i18next';
import './LanguageSelector.css';

export function LanguageSelector() {
  const { i18n } = useTranslation();

  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
    // 保存到 localStorage
    localStorage.setItem('preferred_language', lang);
  };

  const currentLang = i18n.language || 'en';

  const languages = [
    { value: 'en', label: 'EN' },
    { value: 'zh', label: '中文' },
    { value: 'ja', label: '日本語' },
  ];

  return (
    <div className="language-selector">
      <select
        value={currentLang}
        onChange={(e) => changeLanguage(e.target.value)}
        className="language-select"
      >
        {languages.map((lang) => (
          <option key={lang.value} value={lang.value}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  );
}

