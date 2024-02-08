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

entity masked_lut is
--  Port ( );
    port(
        x: in std_logic_vector(K-1 downto 0); --x
        clk: in std_logic;
        reset: in std_logic;
        rnd: in std_logic_vector(K-1 downto 0);
        output: out std_logic_vector(K-1 downto 0));
end masked_lut;

architecture Behavioral of masked_lut is
    component adder_subtractor 
    port (
        x, y: in std_logic_vector(K-1 downto 0);
        addb_sub: in std_logic;
        z: out std_logic_vector(K-1 downto 0)
        );
    end component;
    
    component lut_prime
    port(
        x1: in std_logic_vector(K-1 downto 0);
        x0: in std_logic_vector(K-1 downto 0);
        z: out std_logic_vector(K-1 downto 0)
        );
    end component;
    
--    component random_generator
--    port (
--        clk     : in  std_logic;
--        reset   : in  std_logic;
--        rnd_out : out std_logic_vector(K-1 downto 0)
--    );
--    end component;
    
    signal x1: std_logic_vector(K-1 downto 0);
--    signal x0: std_logic_vector(K-1 downto 0);
    signal lut_prime_x1: std_logic_vector(K-1 downto 0);

begin
    modulo_subtractor_1: adder_subtractor port map (
        x => x,
        y => rnd, --for tcl
        addb_sub => '1',
        z => x1
    ); 
    
--    random_generator_1: random_generator port map (
--        clk => clk,
--        reset => reset,
--        rnd_out => x0
--    );
     
    lut_prime_1: lut_prime port map (
        x1 => x1,
        x0 => rnd,   --for tcl
        z => lut_prime_x1
    );
    
    output <= std_logic_vector(signed(lut_prime_x1) + signed(rnd));
    
end Behavioral;
