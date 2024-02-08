----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/20 23:43:07
-- Design Name: 
-- Module Name: random_generator_tb - Behavioral
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
use work.my_package.all;

-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
--use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity random_generator_tb is

end entity;

architecture behavior of random_generator_tb is 
    -- Component Declaration for the Unit Under Test (UUT)
    component random_generator
        port (
            clk     : in  std_logic;
            reset   : in  std_logic;
            rnd_out : out std_logic_vector(K-1 downto 0)
        );
    end component;
   
    --Inputs
    signal clk   : std_logic := '0';
    signal reset : std_logic := '1';

    --Outputs
    signal rnd_out : std_logic_vector(7 downto 0);

    -- Clock period definitions
    constant clk_period : time := 10 ns;

begin 

    dut: random_generator 
         port map (
           clk => clk,
           reset => reset,
           rnd_out => rnd_out
         );

    -- Clock process definitions
    clk_process :process
    begin
        clk <= '0';
        wait for clk_period/2;
        clk <= '1';
        wait for clk_period/2;
    end process;

    -- Stimulus process
    stim_proc: process
    begin       
        -- Apply reset
        reset <= '1';
        wait for 20 ns;  
        reset <= '0';

        -- Let it run for some cycles
        wait for 1000 ns;

        -- Complete the simulation
        wait;
    end process;

END;
