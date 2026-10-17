# Heritage Discovery Hack Project

A premium, cinematic 3D heritage discovery experience built with React + TypeScript + Three.js/React Three Fiber + Framer Motion + Tailwind CSS.

## Overview

This project implements a modern frontend for the Heritage Discovery backend, enabling users to:
- Upload photos of heritage sites for visual recognition
- Explore a curated catalogue of global heritage locations
- Interact with 3D globe visualizations
- Read preservation stories and evidence

The implementation follows the Front-end-plan.md design specification and showcases advanced React, Three.js, and animation techniques.

## Architecture

### Framework & Libraries
- **React 19** with **React Three Fiber** for 3D integration
- **Zustand** for state management
- **Framer Motion** for animations and transitions
- **Three.js** for 3D graphics
- **Tailwind CSS** with utility-first styling
- **Vite** for build tooling

### Component Structure
```
App
├── LoadingScreen (cinematic birds + particles)
├── Navigation (floating, transparent)
├── HeroSection (3D monument + birds + parallax)
├── Section2 (Recognition UI)
├── Section3 (Heritage Cards)
├── Section4 (3D Globe/Map)
├── Section5 (Preservation)
└── Footer
```

### Key Features
- **Cinematic loading** with birds, particles, fog
- **3D monument visualization** with interactive birds
- **Vertical scroll journey** through five sections
- **Premium UI** with glassmorphism and heritage aesthetics
- **Responsive design** (mobile-first)
- **Performance optimized** with GPU-friendly animations

### Backend Integration
- **POST /recognize** - Heritage site image recognition
- **GET /health** - Service health check
- Direct API integration for real-time recognition results

## Technical Implementation

### Build System
- **Vite** with TypeScript support
- **Tailwind CSS** for styling
- **ESBuild** for bundling
- **Compression** (gzip/brotli) for production
- **ESLint** for code quality

### 3D Components
- **React Three Fiber** integration
- **Procedural monument** generation
- **Floating birds** with flocking behavior
- **Interactive globe** visualization
- **Performance optimized** with LOD

### Animations
- **Framer Motion** for all animations
- **Scroll-triggered reveals**
- **Parallax effects**
- **Micro-interactions**
- **Reduced motion support**

### Design System
- **Color palette** based on heritage gold/silver/ink
- **Typography**: Playfair Display, Cormorant Garamond (headings), Inter, Manrope (body)
- **3D elements** with high detail
- **Accessibility** compliant

## Development

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview built site
npm run preview

# Run tests
npm run test

# Lint code
npm run lint
```

### Production Build
- **TypeScript** compilation
- **Vite** bundling with optimizations
- **CSS extraction** and minification
- **Image optimization**
- **Compression** enabled

### Technologies Used
- **Frontend**: React, TypeScript, Three.js, Framer Motion, Tailwind CSS
- **Build Tools**: Vite, ESBuild, PostCSS
- **State Management**: Zustand
- **Animation**: Framer Motion
- **Styling**: Tailwind CSS
- **Testing**: Vitest

## Quality Features

### Performance
- **Level of Detail (LOD)** for 3D objects
- **Object pooling** for particles
- **Frustum culling** for off-screen elements
- **Frame rate** monitoring
- **Reduced motion** support

### Accessibility
- **WCAG 2.1 AA** compliance
- **Keyboard navigation**
- **Screen reader support**
- **Focus management**
- **Reduced motion preferences**

### Visual Excellence
- **Design system** with tokens
- **Responsive breakpoints**
- **Cross-device compatibility**
- **Performance monitoring**
- **Quality assurance**

## Project Structure

```
Hack/
├── src/
│   ├── components/           # React components
│   │   ├── 3d/               # 3D components
│   │   ├── sections/          # Section components
│   │   ├── cards/             # Card components
│   │   └── ...
│   ├── lib/                  # Library code
│   ├── store/                # State management
│   ├── styles/               # CSS/Styling
│   └── main.tsx             # Entry point
├── .eslint.config.js         # ESLint configuration
├── .gitignore               # Git ignore
├── .vimrc (optional)         # Editor config
├── package.json             # Dependencies
├── README.md                # This file
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Build configuration
└── ...
```

## Notes

### Environment Variables
- `VITE_API_BASE_URL` - Backend API base URL (defaults to `/api`)

### Development
- The dev server runs on `http://localhost:5173/`
- Hot module replacement enabled for fast iteration
- Browser reloads on code changes

### Production
- Built files are in the `dist/` directory
- Static assets served via Vite
- Compression enabled for production

## Future Enhancements

### Optional Features
- **3D monument detail** pages
- **Social sharing** features
- **Offline support** with Service Workers
- **Custom domain integration**
- **Analytics integration**

### Performance Optimizations
- **Code splitting** for lazy loading
- **Advanced caching** strategies
- **Asset optimization**
- **Server-side rendering** (SSR)

## License
MIT. Take it, change it, ship it.

## Acknowledgements
Based on the Heritage Discovery backend API at `backend/api.py` and visual embedding module at `ml/visual_embedding.py`.

Made with ❤️ for heritage discovery.