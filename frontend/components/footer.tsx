"use client";

import Link from "next/link";

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white p-4 mt-auto">
      <div className="container mx-auto text-center">
        <div className="flex justify-center space-x-4 mb-2">
          <Link href="/guides" className="hover:text-gray-300">使用指南</Link>
          <Link href="/faq" className="hover:text-gray-300">常见问题</Link>
          <Link href="/contact" className="hover:text-gray-300">联系我们</Link>
        </div>
        <p className="text-sm text-gray-500">© {new Date().getFullYear()} Boss-Agent. All Rights Reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;
