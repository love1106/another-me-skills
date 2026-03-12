---
name: landing-page-builder
description: >
  Build stunning, modern landing pages with Next.js 15, Framer Motion, and Tailwind CSS.
  Use when: creating landing pages, marketing pages, product pages, or any page
  that needs to impress visitors with beautiful design and smooth animations.
  NOT for: dashboards, admin panels, CRUD apps, or data-heavy interfaces.
---

# Landing Page Builder

Build landing pages that convert. Modern design, smooth animations, mobile-first.

## Stack

- **Next.js 15** (App Router)
- **Tailwind CSS 4** (utility-first styling)
- **Framer Motion** (scroll animations, transitions, gestures)
- **Lucide React** (icons)
- **Inter / Plus Jakarta Sans** (typography via next/font)

## Setup

```bash
npx create-next-app@latest landing --typescript --tailwind --app --src-dir
cd landing
npm install framer-motion lucide-react
```

## Design Principles

1. **Above the fold matters most** — Hero must hook in 3 seconds
2. **Whitespace is premium** — generous padding, don't cram
3. **One CTA per section** — clear action, no confusion
4. **Mobile-first** — design for 375px, scale up
5. **Performance** — no heavy images without optimization, lazy load below fold
6. **Dark mode ready** — design with both themes in mind

## Page Structure (Standard Landing Page)

```
1. Navbar          — Logo + nav links + CTA button (sticky)
2. Hero            — Headline + subtext + CTA + visual/mockup
3. Social Proof    — Logos / "Trusted by" / stats
4. Features        — 3-6 features with icons, grid layout
5. How It Works    — 3-step process, numbered
6. Testimonials    — Quote cards, avatar + name + role
7. Pricing         — 2-3 tiers, highlight recommended
8. FAQ             — Accordion style
9. CTA Section     — Final push, gradient background
10. Footer         — Links + social + copyright
```

## Animation Patterns (Framer Motion)

### Fade In Up (most common — use for section entries)
```tsx
import { motion } from "framer-motion";

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

<motion.div
  initial="hidden"
  whileInView="visible"
  viewport={{ once: true, margin: "-100px" }}
  variants={fadeInUp}
>
  {children}
</motion.div>
```

### Stagger Children (for grids — features, pricing cards)
```tsx
const container = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

<motion.div
  initial="hidden"
  whileInView="visible"
  viewport={{ once: true }}
  variants={container}
  className="grid grid-cols-1 md:grid-cols-3 gap-8"
>
  {features.map((f) => (
    <motion.div key={f.title} variants={item}>
      <FeatureCard {...f} />
    </motion.div>
  ))}
</motion.div>
```

### Scale on Hover (for cards, buttons)
```tsx
<motion.div
  whileHover={{ scale: 1.02, y: -4 }}
  transition={{ type: "spring", stiffness: 300 }}
  className="rounded-2xl border bg-card p-6"
>
  {children}
</motion.div>
```

### Scroll Progress Bar
```tsx
import { motion, useScroll } from "framer-motion";

function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  return (
    <motion.div
      className="fixed top-0 left-0 right-0 h-1 bg-primary z-50 origin-left"
      style={{ scaleX: scrollYProgress }}
    />
  );
}
```

### Counter Animation (for stats)
```tsx
import { useInView, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useRef } from "react";

function AnimatedCounter({ target, suffix = "" }: { target: number; suffix?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v));
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (!isInView) return;
    const controls = animate(count, target, { duration: 2, ease: "easeOut" });
    const unsub = rounded.on("change", (v) => setDisplay(v.toLocaleString()));
    return () => { controls.stop(); unsub(); };
  }, [isInView, target]);

  return <span ref={ref}>{display}{suffix}</span>;
}
```

### Text Reveal (for hero headlines)
```tsx
function TextReveal({ text }: { text: string }) {
  const words = text.split(" ");
  return (
    <motion.h1
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
      className="text-5xl md:text-7xl font-bold tracking-tight"
    >
      {words.map((word, i) => (
        <motion.span
          key={i}
          className="inline-block mr-[0.25em]"
          variants={{
            hidden: { opacity: 0, y: 40, filter: "blur(8px)" },
            visible: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.5 } },
          }}
        >
          {word}
        </motion.span>
      ))}
    </motion.h1>
  );
}
```

### Parallax Section
```tsx
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

function ParallaxSection({ children }: { children: React.ReactNode }) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [100, -100]);

  return (
    <div ref={ref} className="relative overflow-hidden">
      <motion.div style={{ y }}>{children}</motion.div>
    </div>
  );
}
```

## Component Patterns

### Sticky Navbar with Blur
```tsx
"use client";
import { motion, useScroll, useTransform } from "framer-motion";

export function Navbar() {
  const { scrollY } = useScroll();
  const bgOpacity = useTransform(scrollY, [0, 100], [0, 0.8]);
  const borderOpacity = useTransform(scrollY, [0, 100], [0, 0.1]);

  return (
    <motion.header
      className="fixed top-0 inset-x-0 z-50"
      style={{
        backgroundColor: useTransform(bgOpacity, (v) => `rgba(0,0,0,${v})`),
        borderBottom: useTransform(borderOpacity, (v) => `1px solid rgba(255,255,255,${v})`),
        backdropFilter: "blur(12px)",
      }}
    >
      <nav className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
        <Logo />
        <div className="hidden md:flex items-center gap-8 text-sm">
          <a href="#features" className="text-muted-foreground hover:text-foreground transition">Features</a>
          <a href="#pricing" className="text-muted-foreground hover:text-foreground transition">Pricing</a>
          <a href="#faq" className="text-muted-foreground hover:text-foreground transition">FAQ</a>
        </div>
        <Button>Get Started</Button>
      </nav>
    </motion.header>
  );
}
```

### Hero Section
```tsx
export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-background to-background" />

      {/* Floating grid/dots pattern */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5" />

      <div className="relative z-10 mx-auto max-w-4xl px-6 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm mb-8"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
          </span>
          Now in public beta
        </motion.div>

        <TextReveal text="Build something people actually want" />

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto"
        >
          The modern platform for teams who ship fast. Beautiful by default,
          powerful when you need it.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.6 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button size="lg" className="px-8 rounded-full text-base">
            Start for free →
          </Button>
          <Button size="lg" variant="outline" className="px-8 rounded-full text-base">
            Watch demo
          </Button>
        </motion.div>
      </div>
    </section>
  );
}
```

### Feature Card with Icon
```tsx
function FeatureCard({ icon: Icon, title, description }: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="group rounded-2xl border bg-card p-6 transition-colors hover:border-primary/30"
    >
      <div className="mb-4 inline-flex rounded-xl bg-primary/10 p-3">
        <Icon className="h-6 w-6 text-primary" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </motion.div>
  );
}
```

### Pricing Card (Highlighted)
```tsx
function PricingCard({ name, price, features, highlighted }: PricingProps) {
  return (
    <motion.div
      whileHover={{ y: -8 }}
      className={cn(
        "relative rounded-2xl border p-8 flex flex-col",
        highlighted && "border-primary bg-primary/5 shadow-2xl shadow-primary/10 scale-105"
      )}
    >
      {highlighted && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-medium text-primary-foreground">
          Most Popular
        </div>
      )}
      <h3 className="text-lg font-semibold">{name}</h3>
      <div className="mt-4 flex items-baseline gap-1">
        <span className="text-4xl font-bold">${price}</span>
        <span className="text-muted-foreground">/mo</span>
      </div>
      <ul className="mt-6 space-y-3 flex-1">
        {features.map((f) => (
          <li key={f} className="flex items-center gap-3 text-sm">
            <Check className="h-4 w-4 text-primary flex-shrink-0" />
            {f}
          </li>
        ))}
      </ul>
      <Button className={cn("mt-8 w-full rounded-full", highlighted ? "" : "variant-outline")}>
        Get started
      </Button>
    </motion.div>
  );
}
```

### FAQ Accordion
```tsx
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { ChevronDown } from "lucide-react";

function FAQ({ items }: { items: { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <div className="mx-auto max-w-2xl divide-y">
      {items.map((item, i) => (
        <div key={i} className="py-5">
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="flex w-full items-center justify-between text-left"
          >
            <span className="text-base font-medium">{item.q}</span>
            <motion.div animate={{ rotate: open === i ? 180 : 0 }}>
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            </motion.div>
          </button>
          <AnimatePresence>
            {open === i && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <p className="pt-3 text-sm text-muted-foreground leading-relaxed">{item.a}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}
```

## Color & Typography Guidelines

### Color Palette (use CSS variables for theme support)
```css
/* Accent gradient for CTAs and highlights */
.gradient-primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
}

/* Subtle section backgrounds (alternate) */
.section-alt {
  background: hsl(var(--muted) / 0.3);
}

/* Glow effects */
.glow {
  box-shadow: 0 0 80px -20px hsl(var(--primary) / 0.3);
}
```

### Typography Scale
```
Hero headline:    text-5xl md:text-7xl font-bold tracking-tight
Section headline: text-3xl md:text-5xl font-bold tracking-tight
Section subtitle: text-lg md:text-xl text-muted-foreground
Card title:       text-lg font-semibold
Body text:        text-sm md:text-base text-muted-foreground leading-relaxed
Badge/label:      text-xs font-medium uppercase tracking-wider
```

### Spacing
```
Section padding:  py-24 md:py-32
Between sections: gap-24 md:gap-32
Container:        max-w-7xl mx-auto px-6
Card padding:     p-6 md:p-8
Element spacing:  space-y-4 or space-y-6
```

## Visual Enhancement Tricks

### Gradient Text
```tsx
<span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
  Beautiful text
</span>
```

### Animated Gradient Border
```tsx
<div className="relative rounded-2xl p-[1px] bg-gradient-to-r from-primary via-purple-500 to-pink-500">
  <div className="rounded-2xl bg-background p-8">
    Content inside
  </div>
</div>
```

### Floating Dots / Grid Background
```tsx
<div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.05)_1px,transparent_0)] bg-[length:40px_40px]" />
```

### Glassmorphism Card
```tsx
<div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8">
  Content
</div>
```

## Checklist Before Delivery

- [ ] Hero hooks in 3 seconds (headline + CTA clear)
- [ ] Mobile responsive (test 375px, 768px, 1280px)
- [ ] Scroll animations smooth (no jank, `viewport={{ once: true }}`)
- [ ] CTA buttons visible and clear on every viewport
- [ ] Color contrast accessible (text on backgrounds)
- [ ] Loading performance (no layout shift, images optimized)
- [ ] Favicon and meta tags set
- [ ] Dark mode works if enabled
- [ ] All links work (anchor scrolling for same-page)
- [ ] Typography hierarchy clear (one H1, logical H2/H3)

## Anti-Patterns (DON'T)

- ❌ Animation on every element — pick 3-5 key moments
- ❌ Auto-playing video without user consent
- ❌ Tiny text on mobile
- ❌ More than 2 fonts
- ❌ Gradient overload — 1 gradient accent max
- ❌ Generic stock photos — use illustrations or real screenshots
- ❌ Wall of text — bullet points, whitespace
- ❌ Multiple competing CTAs in one section
- ❌ Animations that replay on every scroll (always use `once: true`)
- ❌ Heavy animations on mobile (reduce or disable)
