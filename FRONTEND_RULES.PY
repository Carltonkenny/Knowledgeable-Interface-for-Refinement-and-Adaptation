###As a Senior Frontend Design Consultant, I appreciate your focus on building a robust, systemized knowledge base for your AI agent. Standardizing these practices is the exact right move for scaling quality UI/UX.

Before we dive in, I must be completely candid about my AI nature: I cannot browse the internet to watch or extract text and specific timestamps from the Instagram reels you provided (DUEjWRukT_2, DVC2fsoiEFC, etc.). However, based on my extensive training in React/Vue architecture, UI/UX best practices, and the typical content of high-level frontend design tutorials, I have synthesized a comprehensive, industry-standard skill document.

This document is engineered to serve as the foundational logic for an AI agent tasked with generating and auditing frontend code. It contains 15 actionable rules structured precisely to your specifications.

AI Agent Frontend UI/UX Skill Document & Heuristics
1. Component Granularity & Atomic Design
Explanation: Components must adhere strictly to the Single Responsibility Principle. A component should accomplish one task or render one specific UI element. If a component manages disparate concepts or grows beyond 200-300 lines, it requires subdivision. This principle ensures maximum reusability, simplifies unit testing, and reduces the cognitive load for developers maintaining the codebase. The AI agent must prioritize building up from small "atoms" to complex "organisms."

Examples & Patterns:

Example 1 (React - Atomic Buttons): Instead of standard HTML buttons, use a unified standard: <BaseButton variant="primary" size="lg" icon={<SaveIcon />} onClick={handleSave}>Save</BaseButton>.

Example 2 (Vue - Slot Composability): Utilize slots for layout flexibility: <Card><template #header>Title</template><template #body>Content</template></Card>, preventing the need for massive prop drilling for simple text injections.

Example 3 (Visual Pattern - The UI Library): Isolate UI logic (dropdowns, modals, tooltips) from business logic. The AI should generate a components/ui folder for dumb, presentation-only components.

Common Anti-Pattern to Avoid: The "God Component" – a single, monolithic file (e.g., Dashboard.tsx) that fetches data, manages global state, defines unique inline styles for generic elements, and stretches to 1,000+ lines.

2. State Management Locality
Explanation: State should live as close to where it is used as possible. Pushing all state to a global store (like Redux or Pinia) creates unnecessary overhead and tight coupling. The AI agent must evaluate whether state is purely local (UI toggles), shared amongst siblings (feature-level state), or truly global (user authentication, themes).

Examples & Patterns:

Example 1 (React - Local State): For a simple accordion toggle, use const [isOpen, setIsOpen] = useState(false) inside the specific accordion item, not in a parent Context.

Example 2 (Vue - Provide/Inject): For a complex multi-step form, use provide() at the form wrapper level and inject() in the step components, avoiding Vuex/Pinia for transient form data.

Example 3 (Visual Pattern - Component Trees): Visualize the DOM tree. If state is only needed by Node C and its child Node D, the state should live in Node C, not in the Root Node.

Common Anti-Pattern to Avoid: "Prop Drilling" – passing a simple state variable (like isModalOpen) through five layers of intermediate components that do not care about or use that state, just to reach a deeply nested child.

3. Accessible Form Validation (a11y & UX)
Explanation: Form validation must be immediate, non-punitive, and fully accessible to screen readers. Users should know exactly what went wrong and how to fix it without guessing. The AI agent must always pair visual cues (red borders) with semantic text cues (aria-invalid, aria-describedby) to ensure a robust user experience across all demographics.

Examples & Patterns:

Example 1 (React Hook Form + Zod): Implement schema validation. When an error occurs, map it directly to the input: <input aria-invalid={errors.email ? "true" : "false"} aria-describedby="email-error" />.

Example 2 (Visual Pattern - Inline Feedback): Show validation errors immediately below the input field after the user has blurred (left) the field, not while they are typing the first character.

Example 3 (Vue - Accessible Alerts): Use role="alert" or aria-live="polite" on the error message container so screen readers announce the error immediately when it appears on screen: <span id="email-error" role="alert">{{ errorMessage }}</span>.

Common Anti-Pattern to Avoid: Relying solely on color (e.g., turning a field red) to indicate an error, and popping up a generic browser alert() or a vague toast notification saying "Form submission failed" without highlighting the specific fields.

4. Semantic HTML Architecture
Explanation: Proper HTML semantics are the foundation of SEO and accessibility. The AI agent must choose the most descriptive tag available for a given piece of content rather than relying on generic containers. This aids machine readability (search engines) and human accessibility (assistive technologies), while also making the CSS styling process more intuitive.

Examples & Patterns:

Example 1 (Structural Tags): Use <header>, <main>, <article>, <aside>, and <footer> to create a logical page outline, replacing generic wrapper <div>s.

Example 2 (Interactive Tags): Use <button> for actions that trigger JavaScript logic on the page, and <a> for actions that navigate to a new URL. Never mix them.

Example 3 (Visual Pattern - List Data): When rendering a series of similar items (like a grid of products), wrap them in a <ul> and render each item as an <li>, rather than just stacking <div> elements.

Common Anti-Pattern to Avoid: "Div Soup" – constructing entire pages using nothing but <div> and <span> tags with classes attached, completely ignoring interactive semantics like <button onClick={...}> vs <div onClick={...}> (which lacks keyboard focus and enter-key support).

5. CSS Utility and Scoping (Design Tokens)
Explanation: CSS must be modular, scalable, and devoid of magic numbers. The AI agent should utilize design tokens (CSS variables) for all colors, spacing, and typography. Whether using Tailwind CSS, CSS Modules, or Styled Components, styles must be scoped to prevent global leaks and ensure predictable rendering across different environments.

Examples & Patterns:

Example 1 (Tailwind / Utility Classes): Use predefined spacing scales (p-4, m-2) to ensure consistent rhythm, rather than arbitrary values like padding: 17px.

Example 2 (React - CSS Modules): Map styles directly to components: import styles from './Button.module.css'; <button className={styles.primary}> to guarantee zero specificity clashes.

Example 3 (Vue - Scoped Styles): Always utilize the <style scoped> attribute in Vue Single File Components unless explicitly defining global typography or reset rules.

Common Anti-Pattern to Avoid: Hardcoding hexadecimal colors and pixel values directly into component styles (e.g., color: #3b82f6; margin-top: 15px). If the brand color changes, finding and replacing these magic strings is a maintenance nightmare.

6. Asynchronous UI States (Loading & Skeletons)
Explanation: The interface must communicate its status to the user during network requests. A blank screen creates anxiety and implies the application is broken. The AI agent must automatically generate loading, error, and success states for any component that relies on asynchronous data fetching.

Examples & Patterns:

Example 1 (React - Suspense): Utilize React Suspense with a fallback UI for lazy-loaded components or data fetching: <Suspense fallback={<SkeletonLoader />}> <DataComponent /> </Suspense>.

Example 2 (Visual Pattern - Skeleton Screens): Instead of a generic spinning wheel, display a "skeleton" layout that mimics the shape of the incoming data (e.g., a gray circle for an avatar, gray bars for text) to reduce perceived wait time.

Example 3 (Vue - Async Components): Use Vue's defineAsyncComponent with a dedicated loading component and error component to handle slow network conditions gracefully.

Common Anti-Pattern to Avoid: Cumulative Layout Shift (CLS). Showing a loading spinner that is 20px high, and then suddenly rendering a 500px high image table, causing the entire page layout to violently jump down once the data arrives.

7. Responsive & Fluid Typography
Explanation: Typography must scale gracefully across viewports. Hardcoded pixel font sizes lead to microscopic text on mobile or absurdly large text on ultrawide monitors. The AI agent should implement fluid typography using relative units (rem, em) and viewport units (vw, vh), often combined with CSS clamp().

Examples & Patterns:

Example 1 (CSS Clamp): Define font sizes that scale with the viewport but respect boundaries: font-size: clamp(1rem, 2.5vw, 1.5rem);.

Example 2 (React/Vue - Typography Components): Create a generic <Heading level="h2"> component that maps to a centralized CSS file defining the responsive scale for h2 elements.

Example 3 (Visual Pattern - The 8pt Grid): Ensure line heights and spacing around typography adhere to an 8-point grid system (e.g., 16px, 24px, 32px) to maintain vertical rhythm on all devices.

Common Anti-Pattern to Avoid: Using px for font sizes. This overrides the user's browser-level accessibility settings (e.g., if a visually impaired user sets their default browser font size to 24px, a hardcoded 14px style will ignore their preference).

8. Performance via Memoization & Lazy Loading
Explanation: Rendering is expensive. The UI must remain perfectly fluid (60fps). The AI agent must identify computationally heavy operations or components that re-render unnecessarily and apply memoization. Furthermore, assets and routes not immediately required by the user should be code-split and loaded on demand.

Examples & Patterns:

Example 1 (React - useMemo & useCallback): Wrap expensive array sorting algorithms or deeply nested component callbacks in useMemo or useCallback to prevent them from firing on every parent state change.

Example 2 (Vue - Computed Properties): Rely heavily on computed() for derived state. Vue automatically caches computed properties and only updates them when their reactive dependencies change.

Example 3 (Visual Pattern - Lazy Images): Apply loading="lazy" to all <img> tags below the fold, or use Intersection Observers to trigger data fetching only when an element scrolls into view.

Common Anti-Pattern to Avoid: Premature optimization. Wrapping every single variable in useMemo or React.memo(). The overhead of checking the memoized cache can actually be more expensive than just letting a simple, lightweight component re-render.

9. Micro-interactions and Tactile Feedback
Explanation: User interfaces should feel alive and responsive to touch or cursor movements. Micro-interactions are subtle animations that confirm an action has been received. The AI agent should automatically provision hover, focus, active, and disabled states for all interactive elements, utilizing smooth, quick transitions.

Examples & Patterns:

Example 1 (CSS Transitions): Add smooth scaling and color shifts on hover: transition: all 0.2s ease-in-out; &:hover { transform: translateY(-2px); box-shadow: lg; }.

Example 2 (React - Framer Motion): Use animation libraries for layout changes, like animating an item being removed from a list so the surrounding items smoothly slide into place rather than instantly snapping.

Example 3 (Visual Pattern - Ripple Effects/Active States): When a button is clicked (the :active state), it should visually depress or darken slightly to mimic real-world tactile feedback.

Common Anti-Pattern to Avoid: Slow animations. Any transition taking longer than 300ms makes the application feel sluggish and unresponsive. Animations should be subtle and instantaneous (150ms-250ms).

10. Robust Error Boundaries
Explanation: JavaScript errors in the UI should not result in a completely blank white screen ("the white screen of death"). The AI agent must wrap application sections in Error Boundaries to catch rendering errors locally, log them to a monitoring service, and display a fallback UI to the user, allowing them to recover or navigate away safely.

Examples & Patterns:

Example 1 (React - Error Boundary Class): Implement a class component with componentDidCatch to wrap major layout sections, rendering a "Something went wrong" card instead of crashing the whole app.

Example 2 (Vue - onErrorCaptured): Use the onErrorCaptured lifecycle hook in a parent component to catch errors from descendants and toggle a local error state.

Example 3 (Visual Pattern - Graceful Degradation): If a third-party widget (like a social media feed) fails to load, the error boundary should display a subtle retry button exactly where the widget should be, leaving the rest of the dashboard fully functional.

Common Anti-Pattern to Avoid: Allowing unhandled promise rejections or mapping errors (e.g., calling .map() on undefined) to bubble up to the root element, completely unmounting the React/Vue instance and destroying the user session.

11. Dark Mode & Theming Architecture
Explanation: Dark mode is no longer an optional feature; it is an expected user preference. The AI agent must structure CSS using semantic variables rather than hardcoded hex values, allowing for seamless swapping of palettes based on system preferences (prefers-color-scheme) or user toggles.

Examples & Patterns:

Example 1 (CSS Variables): Define themes semantically: :root { --bg-primary: #ffffff; --text-main: #111; } @media (prefers-color-scheme: dark) { :root { --bg-primary: #121212; --text-main: #eee; } }.

Example 2 (Tailwind Dark Mode): Utilize the dark: variant intelligently: <div className="bg-white dark:bg-gray-800 text-black dark:text-white">.

Example 3 (Visual Pattern - Contrast Ratios): Ensure that in both light and dark themes, text-to-background contrast ratios meet WCAG AA standards (4.5:1 for normal text). Pure black text on pure white is often too harsh; use off-whites and dark grays.

Common Anti-Pattern to Avoid: Forgetting to invert images, SVGs, or shadows in dark mode. A bright, glaring white PNG logo or a massive black drop shadow looks broken when the rest of the interface shifts to a dark theme.

12. Defensive Rendering (Null Check Data)
Explanation: APIs are unreliable. Data shapes change. The AI agent must never assume that an object property or an array exists before attempting to render it. Defensive rendering utilizes optional chaining and logical coalescing to prevent runtime crashes caused by missing backend data.

Examples & Patterns:

Example 1 (React - Optional Chaining): Safely access nested data: <h1>{user?.profile?.firstName ?? 'Guest'}</h1>.

Example 2 (Vue - v-if guards): Prevent child components from mounting until data is ready: <UserProfile v-if="user && user.id" :userData="user" />.

Example 3 (Visual Pattern - Empty States): If an array of data is empty, do not just render a blank space. Render a dedicated "Empty State" component (e.g., an illustration of a box with "No messages yet").

Common Anti-Pattern to Avoid: Trusting the TypeScript interface implicitly at runtime. Just because a type says user.name is a string does not mean the backend won't occasionally send null, causing user.name.toUpperCase() to fatally crash the application.

13. Keyboard Navigation and Focus Management
Explanation: Power users and visually impaired users rely heavily on the keyboard to navigate applications. The AI agent must ensure that all interactive elements are reachable via the Tab key, that the focus outline is clearly visible, and that focus is managed intelligently when modals or flyouts open and close.

Examples & Patterns:

Example 1 (CSS Focus Visible): Always define a highly visible focus state: &:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }.

Example 2 (React/Vue - Focus Trapping): When a modal opens, use a focus trap utility to ensure the Tab key cycles only through the modal's inputs, preventing the user from accidentally interacting with the page behind the modal.

Example 3 (Visual Pattern - Skip Links): Implement an invisible "Skip to Main Content" anchor link at the very top of the DOM that becomes visible only on keyboard focus, allowing users to bypass repetitive header navigation.

Common Anti-Pattern to Avoid: Setting outline: none in CSS without providing a custom visual alternative. This completely destroys keyboard navigation, leaving users blind to where their cursor is currently resting.

14. Data Fetching UX (Optimistic Updates)
Explanation: When a user performs an action (like liking a post or deleting an item), they should not have to wait for the server's response to see the visual change. The AI agent should implement optimistic updates: assuming the network request will succeed, updating the UI instantly, and rolling back only if an error occurs.

Examples & Patterns:

Example 1 (React Query / SWR): Utilize caching libraries to mutate the local cache instantly when a user clicks "Like," before the POST request even finishes.

Example 2 (Visual Pattern - Soft Deletes): When a user clicks delete, immediately fade the item out of the list and show a small "Undo" toast notification for 5 seconds before permanently sending the delete request to the server.

Example 3 (Vue - State Mutations): Instantly push a new comment object into the local Vuex/Pinia array when the user hits submit, showing it in a slight "pending" visual state until the server confirms the ID.

Common Anti-Pattern to Avoid: Disabling the entire screen or showing a massive, blocking loading spinner just because the user clicked a "Like" button, completely disrupting their reading flow.

15. Consistent File Structure and Naming Conventions
Explanation: A codebase scales only as well as its file structure allows. The AI agent must enforce a strict, predictable architecture. Grouping files by feature (rather than by file type) drastically improves navigation in large codebases. Naming must be PascalCase for components and camelCase for functions/hooks.

Examples & Patterns:

Example 1 (Feature-Based Architecture): Group related code: /features/authentication/ containing LoginForm.tsx, authHooks.ts, and authStyles.css together, rather than scattering them across global /components, /hooks, and /styles folders.

Example 2 (React - Barrel Exports): Use index.ts files to export components cleanly from folders: import { Button } from '@/components/ui' instead of import Button from '@/components/ui/Button/Button'.

Example 3 (Visual Pattern - Colocation): Tests (Component.test.tsx) and Storybook files (Component.stories.tsx) must sit directly next to the component they are documenting, not in a mirrored directory tree.

Common Anti-Pattern to Avoid: Inconsistent naming. Having files named user-profile.js, UserProfile.vue, and user_card.tsx in the same project destroys searchability and betrays a lack of architectural discipline.