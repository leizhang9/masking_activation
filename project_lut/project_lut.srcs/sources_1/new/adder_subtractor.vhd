----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/20 01:44:22
-- Design Name: 
-- Module Name: adder_subtractor - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description:  reference: http://www.arithmetic-circuits.org/finite-field/index.html
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
----------------------------------------------------------------------------------
----------------------------------------------------------------------------
-- adder subtractor mod M (adder_subtractor.vhd)
--
-- Adds or Subtract two K-bits operands X and Y mod M
----------------------------------------------------------------------------

library ieee; 
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;
use ieee.std_logic_unsigned.all;
use work.my_package.all;

entity adder_subtractor is
port (
  x, y: in std_logic_vector(K-1 downto 0);
  addb_sub: in std_logic;
  z: out std_logic_vector(K-1 downto 0)
);
end adder_subtractor;

architecture rtl of adder_subtractor is
  signal long_x, xor_y, sum1, long_z1, xor_m, sum2: std_logic_vector(K downto 0);
  signal c1, c2, sel: std_logic;
  signal z1, z2: std_logic_vector(K-1 downto 0);

begin

  long_x <= '0' & x;
  xor_gates1: for i in 0 to K-1 generate 
      xor_y(i) <= y(i) xor addb_sub; 
  end generate;
  xor_y(K) <= '0';
  sum1 <= addb_sub + long_x + xor_y;
  c1 <= sum1(K);
  z1 <= sum1(K-1 downto 0);
  long_z1 <= '0' & z1;
  xor_gates2: for i in 0 to k-1 generate
      xor_m(i) <= m(i) xor not(addb_sub);
  end generate;
  xor_m(k) <= '0';
  sum2 <= not(addb_sub) + long_z1 + xor_m;
  c2 <= sum2(k);
  z2 <= sum2(k-1 downto 0);
  sel <= (not(addb_sub) and (c1 or c2)) or (addb_sub and not(c1));
  with sel select z <= z1 when '0', z2 when others;

end rtl;

