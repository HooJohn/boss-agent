"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { useState, useEffect } from "react";
import { useDeviceId } from "@/hooks/use-device-id";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Button } from "./ui/button";
import { History } from "lucide-react";

const Header = () => {
  const pathname = usePathname();
  const { deviceId } = useDeviceId();
  const [sessions, setSessions] = useState<{ id: string; first_message: string }[]>([]);

  const navLinks = [
    { href: "/", label: "助理" },
    { href: "/finance", label: "财务" },
    { href: "/hr", label: "人事" },
  ];

  useEffect(() => {
    if (deviceId) {
      fetch(`/api/sessions/${deviceId}`)
        .then((res) => res.json())
        .then((data) => {
          console.log("Fetched sessions data:", data);
          setSessions(data.sessions || []);
        });
    }
  }, [deviceId]);

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
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <History className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {sessions.map((session) => (
              <DropdownMenuItem key={session.id}>
                <Link href={`/?id=${session.id}`}>{session.first_message || session.id}</Link>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
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
