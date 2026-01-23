import React from "react";
import { Outlet } from "react-router-dom";
import Header from "common/components/Header/Header";

export default function RootLayout() {
  return (
    <>
      <Header showNav={true} showAuthArea={true} />
      <Outlet />
    </>
  );
}
