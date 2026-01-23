import React from "react";
import { Outlet } from "react-router-dom";
import Header from "common/components/Header/Header";

export default function AuthLayout() {
  return (
    <>
      <Header showNav={false} showAuthArea={false} />
      <Outlet />
    </>
  );
}
