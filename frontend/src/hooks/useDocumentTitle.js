import { useEffect } from 'react';

const DEFAULT_TITLE = 'DAREEDA - Dati puri. Flussi solidi.';

export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} | DAREEDA` : DEFAULT_TITLE;
    return () => {
      document.title = DEFAULT_TITLE;
    };
  }, [title]);
}
