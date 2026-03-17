import { Layers2, ScanSearch, Minimize2, Combine, Scissors, FileImage } from "lucide-react";
import { ToolDefinition } from "@/lib/types";

export const toolDefinitions: ToolDefinition[] = [
  {
    slug: "upscale",
    category: "Image",
    title: "AI Image Upscaler",
    description: "AI enhancement is being refined for reliability. The future upscale pipeline is still being prepared behind the scenes.",
    accept: [".png", ".jpg", ".jpeg", ".webp"],
    maxFiles: 1,
    endpoint: "/api/tools/upscale/jobs",
    badge: "Coming soon",
    details: "AI enhancement in progress. CreatorLab is keeping the upscale architecture in place, but the public launch flow is paused until the output quality and reliability are ready.",
    eta: "AI enhancement in progress",
    supportsQualityMode: true,
    available: false,
    availabilityLabel: "Coming soon"
  },
  {
    slug: "background-remove",
    category: "Image",
    title: "Background Remover",
    description: "Cut out products, portraits, and assets into clean transparent PNG exports.",
    accept: [".png", ".jpg", ".jpeg", ".webp"],
    maxFiles: 1,
    endpoint: "/api/tools/background-remove/jobs",
    badge: "PNG export",
    details: "Runs rembg with the u2net model for clean cutouts and transparent PNG exports.",
    eta: "8-20 sec"
  },
  {
    slug: "compress",
    category: "Image",
    title: "Image Compressor",
    description: "Reduce file sizes while keeping strong visual quality for fast delivery.",
    accept: [".png", ".jpg", ".jpeg", ".webp"],
    maxFiles: 1,
    endpoint: "/api/tools/compress/jobs",
    badge: "Smart quality settings",
    details: "Compare original vs compressed output size and download optimized files instantly.",
    eta: "5-10 sec"
  },
  {
    slug: "pdf-merge",
    category: "PDF",
    title: "Merge PDFs",
    description: "Combine multiple PDFs into one clean export in the right order.",
    accept: [".pdf"],
    maxFiles: 10,
    endpoint: "/api/tools/pdf/merge/jobs",
    badge: "Multi-file",
    details: "Simple merge flow with drag-and-drop ordering and a fast combined download.",
    eta: "5-15 sec"
  },
  {
    slug: "pdf-split",
    category: "PDF",
    title: "Split PDF Pages",
    description: "Extract a single page range or split a long PDF into clean multi-file chunks.",
    accept: [".pdf"],
    maxFiles: 1,
    endpoint: "/api/tools/pdf/split/jobs",
    badge: "Range or chunks",
    details: "Choose between extracting one custom page range or splitting the PDF into evenly sized chunk files with optional ZIP download.",
    eta: "5-15 sec"
  },
  {
    slug: "images-to-pdf",
    category: "PDF",
    title: "Images to PDF",
    description: "Turn image sets into polished shareable PDF documents with one export.",
    accept: [".png", ".jpg", ".jpeg", ".webp"],
    maxFiles: 20,
    endpoint: "/api/tools/pdf/images-to-pdf/jobs",
    badge: "Batch convert",
    details: "Perfect for receipts, portfolios, reports, and quick document creation.",
    eta: "5-15 sec"
  }
];

export const toolIcons = {
  upscale: Layers2,
  "background-remove": ScanSearch,
  compress: Minimize2,
  "pdf-merge": Combine,
  "pdf-split": Scissors,
  "images-to-pdf": FileImage
};

export function getToolDefinition(slug: string) {
  return toolDefinitions.find((tool) => tool.slug === slug);
}
