"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

const Header = () => {
  const pathname = usePathname();

  const navLinks = [
    { href: "/", label: "助理" },
    { href: "/finance", label: "财务" },
    { href: "/hr", label: "人事" }, // Assuming /hr for Human Resources
  ];

  return (
    <header className="bg-gray-800 text-white">
      <div className="container mx-auto flex justify-between items-center p-4">
        <div className="flex items-center">
          <Image src="/logo-only.png" alt="Boss-Agent Logo" width={40} height={40} className="mr-4" />
          <div>
            <h1 className="text-xl font-bold">Boss-Agent</h1>
            <p className="text-sm text-gray-400">智能决策，数据驱动的企业报表与分析AI</p>
          </div>
        </div>
      </div>
      <nav className="bg-gray-700">
        <div className="container mx-auto">
          <ul className="flex">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className={`px-4 py-3 text-sm font-medium block ${pathname === link.href ? 'bg-blue-500 text-white' : 'text-gray-300 hover:bg-gray-600'}`}>
                    {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </nav>
    </header>
  );
};

export default Header;
