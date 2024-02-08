----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/20 22:40:26
-- Design Name: 
-- Module Name: lut_tb - Behavioral
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

--correct
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

ENTITY lut_tb IS
END lut_tb;

ARCHITECTURE behavior OF lut_tb IS 

    -- Component Declaration for the Unit Under Test (UUT)
    COMPONENT lut
    PORT(
         index  : IN  std_logic_vector(K-1 downto 0);
         output : OUT std_logic_vector(K-1 downto 0)
        );
    END COMPONENT;
   
    --Inputs
    signal index : std_logic_vector(K-1 downto 0) := (others => '0');

    --Outputs
    signal output : std_logic_vector(K-1 downto 0);

    -- Clock period definitions
    constant clk_period : time := 10 ns;

BEGIN 

    -- Instantiate the Unit Under Test (UUT)
    dut: lut PORT MAP (
          index => index,
          output => output
    );

    -- Stimulus process
    stim_proc: process
    begin       
        -- Apply test vectors
        index <= "00000000"; wait for clk_period;
        index <= "00000001"; wait for clk_period;
        index <= "00000010"; wait for clk_period;
        index <= "00000011"; wait for clk_period;
        index <= "00000100"; wait for clk_period;
        index <= "00000101"; wait for clk_period;
        index <= "00000110"; wait for clk_period;
        -- Add more test vectors as needed
        -- ...

        -- Complete the simulation
        wait;
    end process;

END;