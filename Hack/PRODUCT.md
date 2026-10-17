# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated: React + TypeScript + Vite + React Three Fiber + Framer Motion + Tailwind CSS. Chosen because the user specified React + TypeScript + Three.js/React Three Fiber + Framer Motion/GSAP + Tailwind CSS and Vite is the standard fast scaffold for that stack.

## Users

Primary user: heritage enthusiasts, travelers, and educators who photograph a monument or site and want to identify it and learn its story. They are on mobile or desktop, often in the field, and want a fast, trustworthy answer rather than a generic search result.

## Product Purpose

A frontend for the Heritage Discovery backend that lets a user upload or capture a photo of a heritage site and get back an identification: what the site is, its confidence, supporting evidence, and a natural-language answer to an optional question. The product exists to make visual AI recognition feel immediate, credible, and worth returning to.

## Positioning

The differentiator is the visual AI recognition pipeline: given a photograph, the system returns a matched heritage site with confidence scoring, evidence links, and an answer generated from retrieved context. A general search engine or a static catalogue cannot truthfully copy that closed-loop recognition behaviour.

## Operating Context

- Users upload an image (file or camera capture) or paste a base64 image.
- The frontend calls the backend `POST /recognize` endpoint and displays the result.
- A health check (`GET /health`) is used to confirm the service is ready before recognition.
- The experience is cinematic and scroll-driven, per the front-end rebuild plan, but recognition is the core job.
- Environment: modern browser, desktop and mobile.

## Capabilities and Constraints

- Image upload with client-side validation (size, type, dimensions).
- Display of recognition results: site name, confidence, evidence, and generated answer.
- Optional free-text question alongside the image.
- Cinematic loading, hero, and scroll sections built with React Three Fiber and Framer Motion.
- Must not modify or depend on any existing project files in `frontend_new/`, `backend/`, `ml/`, `data/`, or `scripts/`.
- The new project lives in its own folder `Hack/`.

## Brand Commitments

- Product name: Heritage Discovery.
- Voice: informative, warm, precise; avoids hype and never invents facts not returned by the backend.
- Colour palette (from the front-end plan): charcoal `#05070C`, near-black `#11131A`, off-white `#F2F4F7`, muted `#A5ABB6`, warm gold `#D4B483`, metallic `#C4C7CE`, subtle line `rgba(232, 209, 203, .15)`.
- Typography: Playfair Display + Cormorant Garamond for headings; Inter + Manrope for body.

## Evidence on Hand

- Backend API contract: `GET /health` and `POST /recognize` in `backend/api.py` (read-only inspected; not modified).
- Existing design direction in `Front-end-plan.md` (component structure, colour palette, typography, phases).
- Existing static frontend in `frontend_new/` as an anti-reference, not a template.

## Product Principles

1. The recognition result is the product; everything else serves it.
2. Never invent facts — display only what the backend returns.
3. Make the wait feel intentional, not broken.
4. Cinematic but never at the cost of usability or accessibility.
5. Mobile-first responsive, with reduced effects on low-end devices.

## Accessibility & Inclusion

- WCAG 2.1 AA contrast targets for text on background.
- Keyboard navigable; focus states visible.
- `prefers-reduced-motion` respected — animations disable or simplify when requested.
- Screen-reader-friendly labels on all interactive controls and image uploads.