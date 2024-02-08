----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/19 22:57:58
-- Design Name: 
-- Module Name: lut_prime - Behavioral
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
use ieee.numeric_std.all;
use work.my_package.all;
-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity lut_prime is
--  Port ( );
    port(
        x1: in std_logic_vector(K-1 downto 0);
        x0: in std_logic_vector(K-1 downto 0);
        z: out std_logic_vector(K-1 downto 0));
end lut_prime;

architecture Behavioral of lut_prime is
-- component declaration
    component adder_subtractor 
    port (
        x, y: in std_logic_vector(K-1 downto 0);
        addb_sub: in std_logic;
        z: out std_logic_vector(K-1 downto 0)
        );
    end component;
    
    component lut
    port(
        index: in std_logic_vector(K-1 downto 0);
        output: out std_logic_vector(K-1 downto 0));
    end component;
    
    signal x: std_logic_vector(K-1 downto 0);
    signal lut_x: std_logic_vector(K-1 downto 0);
begin
    modulo_adder_1: adder_subtractor port map (
        x => x1,
        y => x0,
        addb_sub => '0',
        z => x
    );
    
    lut_1: lut port map (
        index => x,
        output => lut_x
    );
    
    z <= std_logic_vector(signed(lut_x) - signed(x0));
   
end Behavioral;
