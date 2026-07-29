/**
 * middleware.ts — NextAuth middleware protecting all (dashboard) routes.
 *
 * Per frontend_architecture.md §2:
 *   "Protected routes under (dashboard) check session via NextAuth middleware
 *    (middleware.ts at project root) — redirect to /login if unauthenticated."
 */

export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/resume/:path*",
    "/skill/:path*",
    "/learning/:path*",
    "/career/:path*",
  ],
};
