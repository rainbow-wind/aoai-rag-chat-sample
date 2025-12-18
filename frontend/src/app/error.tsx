'use client';

import Link from "next/link";
import React from "react";

const ErrorPage = () => {
    return (
        <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
            <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-center py-32 px-16 bg-white dark:bg-black sm:items-start">
                <h1 className="mb-4 text-4xl font-bold text-gray-900 dark:text-white">  
                    An Error Occurred
                </h1>
                <p className="mb-8 text-lg text-gray-700 dark:text-gray-300">
                    Sorry, something went wrong while processing your request.
                </p>
                <Link
                    href="/"
                    className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                >
                    Go back to Home
                </Link>
            </main>
        </div>
    );  
}

export default ErrorPage;