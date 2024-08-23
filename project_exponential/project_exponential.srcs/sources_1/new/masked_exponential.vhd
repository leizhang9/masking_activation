----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 03/18/2024 09:49:28 AM
-- Design Name: 
-- Module Name: masked_exponential - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
----------------------------------------------------------------------------------
library IEEE;
library ieee_proposed;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.all;

use ieee_proposed.fixed_float_types.all;
use ieee_proposed.fixed_pkg.all;
use ieee_proposed.float_pkg.all;
use work.my_package.all;

--entity masked_exponential is
--    Port (
--        x : in sfixed(15 downto -16); -- Input x in Q15.16 format
--        reset: in std_logic;
--        rnd: in std_logic_vector(K-1 downto 0);
--        e_x : out sfixed(31 downto -32)
--    );
--end masked_exponential;
entity masked_exponential is
    port(
        x: in std_logic_vector(K-1 downto 0); --x
        clk: in std_logic;
        reset: in std_logic;
        rnd: in std_logic_vector(K-1 downto 0);
        output: out std_logic_vector(K-1 downto 0));
end masked_exponential;

architecture Behavioral of masked_exponential is
    -- Constants for the computation
    constant ln2 : sfixed(K/2 -1 downto -K/2) := to_sfixed(0.69314718, K/2 -1, -K/2); 
    constant log2e : sfixed(K/2 -1 downto -K/2) := to_sfixed(1.44269504, K/2 -1, -K/2); -- log2(e) approximation
    
    signal x_sfixed: sfixed(K/2 -1 downto -K/2);
    signal rnd_fixed: sfixed(K/2 -1 downto -K/2);
    signal output_sfixed: sfixed(K/2 -1 downto -K/2) := to_sfixed(0, K/2 -1, -K/2);
    
    signal t, k_sfixed : sfixed(K/2 -1 downto -K/2);
    signal m : integer;
    signal two_power_m : sfixed(K/2 -1 downto -K/2);
    signal n : sfixed(K/2 -1 downto -K/2);
    signal e_k : sfixed(K/2 -1 downto -K/2); 
begin
    x_sfixed <= to_sfixed(signed(x), K-1, 0);  --to keep data unchanged
    rnd_fixed <= to_sfixed(signed(rnd), K-1, 0);  -- to keep data unchanged
   
    -- Calculate t = x * log2(e)
    t <= resize(x_sfixed * log2e, t'high, t'low);
    -- Split t into integer part (m) and fractional part (n)
    m <= to_integer(t);
    n <= resize((t - to_sfixed(m, t'high, t'low)), n'high, n'low);
    
    k_sfixed <= resize(n * ln2, k_sfixed'high, k_sfixed'low);
    e_k <= resize((to_sfixed(1, e_k'high, e_k'low) + resize(k_sfixed, e_k'high, e_k'low) + resize((k_sfixed*k_sfixed)/2, e_k'high, e_k'low)), e_k'high, e_k'low);
     
    two_power_m <= SHIFT_LEFT(to_sfixed(2.0, 15, -K/2), m-1);
    output_sfixed <= resize(two_power_m*e_k, output_sfixed'high, output_sfixed'low);
    output <= to_slv(output_sfixed);
end Behavioral;