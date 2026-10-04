import type { Lang } from "../types";

interface Props {
  lang: Lang;
  onChange: (lang: Lang) => void;
}

// 言語選択（ja / en / zh）。変更は App で保存・Accept-Language に反映される
export default function LanguageSwitcher({ lang, onChange }: Props) {
  return (
    <select aria-label="Language" value={lang} onChange={(e) => onChange(e.target.value as Lang)}>
      <option value="ja">日本語</option>
      <option value="en">English</option>
      <option value="zh">中文</option>
    </select>
  );
}
