/**
 * Gallery data schema.
 * Each entry represents a pre-computed Leit signature for a famous repository.
 * Audio files are hosted in Azure Blob Storage.
 */

export interface GalleryEntry {
  /** URL-friendly identifier, e.g. "react", "linux", "vscode" */
  slug: string;
  /** Display name, e.g. "React" */
  name: string;
  /** GitHub owner/repo */
  repo: string;
  /** Short description */
  description: string;
  /** Primary language */
  language: string;
  /** Approximate GitHub stars (at time of generation) */
  stars: number;
  /** Commit SHA that was analyzed */
  commit_sha: string;
  /** Date the signature was generated (ISO string) */
  generated_at: string;
  /** Detected genre */
  genre: string;
  /** BPM */
  tempo: number;
  /** Musical key */
  key: string;
  /** Azure Blob Storage URLs */
  audio: {
    wav: string;
    midi: string;
    ai_generated?: string;
  };
  /** Path to logo in public/images/ */
  logo: string;
  /** Selected metrics for the card display */
  metrics: {
    complexity_score: number;
    maintainability_score: number;
    coupling_score: number;
    module_count: number;
  };
}

export interface GalleryData {
  /** Base URL for Azure Blob Storage container */
  storage_base_url: string;
  entries: GalleryEntry[];
}
