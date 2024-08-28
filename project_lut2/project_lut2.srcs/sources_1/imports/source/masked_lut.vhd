----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/19 01:34:22
-- Design Name: 
-- Module Name: masked_lut - Behavioral
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
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use ieee.numeric_std.all;
use work.my_package.all;
-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

-------for dump
-------new interface, x0 and x1 as input instead of x and x0
-----------------------------------------
-----------------------------------------
entity masked_lut is
    port(
        x0: in std_logic_vector(K-1 downto 0);
        x1: in std_logic_vector(K-1 downto 0); --x1
        m: in std_logic_vector( K-1 downto 0);
        clk: in std_logic;
        reset: in std_logic;
        output: out std_logic_vector(K-1 downto 0));
end masked_lut;

architecture dump of masked_lut is
    
    component lut_prime
    generic(lut_size : integer);
    port(
        clk: in std_logic;
        x0: in std_logic_vector(K-1 downto 0);
        x1: in std_logic_vector(K-1 downto 0);
        m: in std_logic_vector(K-1 downto 0);
        z: out std_logic_vector(K-1 downto 0)
        );
    end component;
   
    signal lut_prime_x1: std_logic_vector(K-1 downto 0);
    attribute keep: string;
    attribute keep of x0: signal is "true";
    attribute keep of x1: signal is "true";
    attribute keep of m: signal is "true";
    
    attribute DONT_TOUCH: string;
    attribute DONT_TOUCH of lut_prime_1: label is "true";
begin
    
    lut_prime_1: lut_prime generic map(lut_size => my_size)
        port map (
        clk => clk,
        x0 => x0,
        x1 => x1,
        m => m,
        z => lut_prime_x1
    );
    
    output <= std_logic_vector(signed(lut_prime_x1) + signed(m));
    
end dump;
