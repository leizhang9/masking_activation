----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 03/19/2024 11:06:47 AM
-- Design Name: 
-- Module Name: masked_exponential_tb - Behavioral
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
use IEEE.NUMERIC_STD.ALL;

use ieee_proposed.fixed_float_types.all;
use ieee_proposed.fixed_pkg.all;
use ieee_proposed.float_pkg.all;
use work.my_package.all;

entity masked_exponential_tb is
end masked_exponential_tb;

architecture tb of masked_exponential_tb is
    -- Component declaration for the exp_calculator
    component masked_exponential is
    port(
        x: in std_logic_vector(K-1 downto 0); --x
        clk: in std_logic;
        reset: in std_logic;
        rnd: in std_logic_vector(K-1 downto 0);
        output: out std_logic_vector(K-1 downto 0));
    end component;
    
    -- Signals for the testbench
    --Inputs
    signal x: std_logic_vector(K-1 downto 0);
    signal clk   : std_logic := '0';
    signal reset : std_logic := '1';
    signal rnd : std_logic_vector(K-1 downto 0);  --for tcl
    --Outputs
    signal output : std_logic_vector(K-1 downto 0);

    -- Clock period definitions
    constant clk_period : time := 10 ns;
    
    
begin
    UUT: masked_exponential
        Port map (
            x => x,
            clk => clk,
            reset => reset,
            output => output,
            rnd => rnd   --for tcl
        );

    -- Clock process
--    clocking: process
--    begin
--        while true loop
--            tb_clk <= '0';
--            wait for 10 ns; -- Adjust clock period as necessary
--            tb_clk <= '1';
--            wait for 10 ns;
--        end loop;
--    end process;
    
    
    -- Test process
    testing: process
    begin
        
        x <= to_slv(to_sfixed(-50, 15, -16));
        wait for 20 ns;
        
        x <= to_slv(to_sfixed(-25, 15, -16));
        wait for 20 ns;
        
        x <= to_slv(to_sfixed(-10.7, 15, -16));
        wait for 20 ns;
        -- Test 1: x = 0 (e^0 should be 1)
        x <= to_slv(to_sfixed(0.0, 15, -16));
        wait for 20 ns;
        
        -- Test 2: x = 1 (e^1 should be approximately 2.7182818)
        x <= to_slv(to_sfixed(1.0, 15, -16));
        wait for 20 ns;
        
        -- Test 3: x = 1.5 (e^1.5 should be approximately 4.481689)
        x <= to_slv(to_sfixed(1.5, 15, -16));
        wait for 20 ns;
        
        x <= to_slv(to_sfixed(5, 15, -16));
        wait for 20 ns;
        
        x <= to_slv(to_sfixed(10.7, 15, -16));
        wait for 20 ns;
        
        x <= to_slv(to_sfixed(50, 15, -16));
        wait for 20 ns;
        
        wait;
    end process;
end tb;




