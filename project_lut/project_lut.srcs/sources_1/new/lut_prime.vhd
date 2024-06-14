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
    generic(lut_size:integer);
    port(
        clk: in std_logic;
        x1: in std_logic_vector(K-1 downto 0);
        x0: in std_logic_vector(K-1 downto 0);
        z: out std_logic_vector(K-1 downto 0));
end lut_prime;

-----------------------------------------------
-------------------------------------------------
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
    generic(lut_size: integer);
    port(
        index: in std_logic_vector(K-1 downto 0);
        output: out std_logic_vector(K-1 downto 0));
    end component;
    
    type type_array is array (0 to lut_size - 1) of std_logic_vector(K-1 downto 0);
    signal x_array : type_array := (others => (others => '0'));
    signal lut_x_array : type_array := (others => (others => '0'));
    signal z_array : type_array := (others => (others => '0'));
    
    type type_array_integer is array (0 to lut_size - 1) of integer;
    signal x1_array : type_array_integer := (others => 0);

    function initialize return type_array_integer is
        variable tmp_array : type_array_integer;
    begin
        for i in 0 to lut_size - 1 loop
            tmp_array(i) := i;
        end loop;
        return tmp_array;
    end function;
    
begin

    x1_array <= initialize;

    lut_instance: for i in 0 to lut_size-1 generate
        lut_i: lut generic map(lut_size => lut_size)  
        port map (
            index => x_array(i),
            output => lut_x_array(i)
        );
    end generate;
    
    assignment: for i in 0 to lut_size-1 generate
        p: process(all)
        begin
            x_array(i) <= std_logic_vector(to_unsigned(( x1_array(i) + to_integer(unsigned(x0))) mod my_size, 8));
            z_array(i) <= std_logic_vector(to_signed(to_integer(signed(lut_x_array(i))) - to_integer(unsigned(x0)), 8));
        end process;
    end generate;
    
    --look up table prime
    z <= z_array(to_integer(unsigned(x1)));
   
end Behavioral;

----------------------------------------------------------
----------------------------------------------------------
--architecture sequential of lut_prime is
---- component declaration
--    component adder_subtractor 
--    port (
--        x, y: in std_logic_vector(K-1 downto 0);
--        addb_sub: in std_logic;
--        z: out std_logic_vector(K-1 downto 0)
--        );
--    end component;
    
--    component lut
--    generic(lut_size: integer);
--    port(
--        index: in std_logic_vector(K-1 downto 0);
--        output: out std_logic_vector(K-1 downto 0));
--    end component;
    
--    type type_array is array (0 to lut_size - 1) of std_logic_vector(K-1 downto 0);
--    signal out_array : type_array := (others => (others => '0'));
--    signal x: std_logic_vector(K-1 downto 0) := (others => '0');
--    signal lut_x: std_logic_vector(K-1 downto 0) := (others => '0');
    
--begin
--    lut_i: lut generic map(lut_size => lut_size)  
--        port map (
--            index => x,
--            output => lut_x
--        );
        
--    process
--    begin
--        wait on x0;
--        for i in 0 to lut_size-1 loop              
--            x <=  std_logic_vector( to_unsigned( (to_integer(unsigned(x0)) + i) mod my_size, 8) );
--            wait until rising_edge(clk);
--            out_array(i) <= std_logic_vector(to_unsigned( to_integer(unsigned(lut_x)) - to_integer(unsigned(x0)) , 8) );
--        end loop;
--    end process;
    
--    z <= out_array(to_integer(unsigned(x1)));
    
--end sequential;