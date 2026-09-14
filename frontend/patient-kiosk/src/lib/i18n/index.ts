import { en } from "./en";
import { hi } from "./hi";

export type Language = "en" | "hi";
export type TranslationKey = keyof typeof en;

const dictionaries = {
  en,
  hi,
};

export function getTranslation(lang: Language) {
  return dictionaries[lang];
}

// A simple hook or function to get translation based on current language
// In a real app, this would use Context to get the current language.
// We'll pass `lang` explicitly for simplicity in our context hook.
